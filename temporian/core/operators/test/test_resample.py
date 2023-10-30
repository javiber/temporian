# Copyright 2021 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math

from absl.testing import absltest
from absl.testing.parameterized import TestCase

from temporian.implementation.numpy.data.io import event_set
from temporian.test.utils import assertOperatorResult


class Resampleest(TestCase):
    def test_basic(self):
        evset = event_set(
            timestamps=[1, 5, 8, 9, 1, 1],
            features={
                "a": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                "b": [5, 6, 7, 8, 9, 10],
                "c": ["A", "B", "C", "D", "E", "F"],
                "x": [1, 1, 1, 1, 2, 2],
            },
            indexes=["x"],
        )
        sampling = event_set(
            timestamps=[-1, 1, 6, 10, 2, 2, 1],
            features={"x": [1, 1, 1, 1, 2, 2, 3]},
            indexes=["x"],
        )

        result = evset.resample(sampling)

        expected = event_set(
            timestamps=[-1, 1, 6, 10, 2, 2, 1],
            features={
                "a": [math.nan, 1.0, 2.0, 4.0, 6.0, 6.0, math.nan],
                "b": [0, 5, 6, 8, 10, 10, 0],
                "c": ["", "A", "B", "D", "F", "F", ""],
                "x": [1, 1, 1, 1, 2, 2, 3],
            },
            indexes=["x"],
            same_sampling_as=sampling,
        )

        assertOperatorResult(self, result, expected)


if __name__ == "__main__":
    absltest.main()
