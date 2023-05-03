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

from absl.testing import absltest
import numpy as np
import pandas as pd

from temporian.core.operators.calendar.iso_week import (
    CalendarISOWeekOperator,
)
from temporian.implementation.numpy.data.event_set import IndexData
from temporian.implementation.numpy.data.event_set import EventSet
from temporian.implementation.numpy.operators.calendar.iso_week import (
    CalendarISOWeekNumpyImplementation,
)


class CalendarISOWeekNumpyImplementationTest(absltest.TestCase):
    """Test numpy implementation of calendar_iso_week operator."""

    def test_basic(self) -> None:
        "Basic test with flat node."
        input_evset = EventSet.from_dataframe(
            pd.DataFrame(
                data=[
                    [
                        pd.to_datetime("1970-01-01", utc=True)
                    ],  # Thursday, so ISO week 1 goes until Sunday 4th
                    [
                        pd.to_datetime("1970-01-04", utc=True)
                    ],  # Sunday, still ISO week 1
                    [
                        pd.to_datetime("1970-01-05", utc=True)
                    ],  # Monday, ISO week 2
                    [
                        pd.to_datetime("2023-01-01", utc=True)
                    ],  # Sunday, ISO week 52 (week 1 is the first to contain a Thursday)
                    [
                        pd.to_datetime("2023-01-08", utc=True)
                    ],  # Sunday, ISO week 1
                    [
                        pd.to_datetime("2023-01-09", utc=True)
                    ],  # Monday, ISO week 2
                    [pd.to_datetime("2023-03-24", utc=True)],  # ISO week 12
                    [pd.to_datetime("2023-12-31", utc=True)],  # ISO week 52
                ],
                columns=["timestamp"],
            ),
        )
        input_node = input_evset.node()
        output_evset = EventSet(
            data={
                (): IndexData(
                    [np.array([1, 1, 2, 52, 1, 2, 12, 52]).astype(np.int32)],
                    input_evset.first_index_data().timestamps,
                ),
            },
            feature_names=["calendar_iso_week"],
            index_names=[],
            is_unix_timestamp=True,
        )
        operator = CalendarISOWeekOperator(input_node)
        impl = CalendarISOWeekNumpyImplementation(operator)
        output = impl.call(sampling=input_evset)

        self.assertTrue(output_evset == output["node"])
        self.assertTrue(
            output["node"].first_index_data().features[0].dtype == np.int32
        )


if __name__ == "__main__":
    absltest.main()
