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

"""Feature class definition."""

from typing import Any, Optional

from temporian.core.data import sampling as sampling_lib
from temporian.core.data import dtype as dtype_lib


class Feature(object):
    """Feature values for a certain sampling.

    A feature can be thought of as a list of univariate series, where each item
    in the list corresponds to an index value in the feature's sampling and each
    value in that item corresponds to a timestamp in it.

    A feature holds no actual data, but rather describes the structure (or
    "schema") of data during evaluation.

    Attributes:
        creator: the operator that created this feature. Can be None if it
            wasn't created by an operator.
        dtype: the feature's data type.
        name: The name of the feature.
        sampling: The feature's sampling.
    """

    def __init__(
        self,
        name: str,
        dtype: Any = dtype_lib.FLOAT32,
        sampling: Optional[sampling_lib.Sampling] = None,
        creator: Optional[Any] = None,
    ):
        # TODO: Find a simple, efficient and consistant way to check the type
        # of arguments in the API.
        assert isinstance(
            name, str
        ), f"`name` must be a string. Got name={name} instead."
        assert sampling is None or isinstance(
            sampling, sampling_lib.Sampling
        ), (
            "`sampling` must be None or a Sampling. Got"
            f" sampling={sampling} instead."
        )

        if dtype not in dtype_lib.ALL_TYPES:
            raise ValueError(
                f"Invalid dtype feature constructor. Got {dtype}. "
                f"Expecting one of {dtype_lib.ALL_TYPES} instead."
            )

        self._name = name
        self._sampling = sampling
        self._dtype = dtype
        self._creator = creator

    def __repr__(self):
        return (
            f"name: {self._name}\n"
            f"  dtype: {self._dtype}\n"
            f"  sampling: {self._sampling}\n"
            f"  creator: {self.creator()}\n"
            f"  id: {id(self)}"
        )

    def name(self) -> str:
        return self._name

    def dtype(self):
        return self._dtype

    def sampling(self) -> Optional[sampling_lib.Sampling]:
        return self._sampling

    def creator(self):
        return self._creator

    def set_sampling(self, sampling: sampling_lib.Sampling):
        self._sampling = sampling

    def set_creator(self, creator):
        self._creator = creator
