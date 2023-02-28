from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd

from temporian.core.data.event import Event
from temporian.core.data.feature import Feature
from temporian.core.data import dtype
from temporian.implementation.numpy.data.sampling import NumpySampling

DTYPE_MAPPING = {
    np.float64: dtype.FLOAT64,
    np.float32: dtype.FLOAT32,
    np.int64: dtype.INT64,
    np.int32: dtype.INT32,
}


class NumpyFeature:
    def __init__(self, name: str, data: np.ndarray) -> None:
        if len(data.shape) > 1:
            raise ValueError(
                "NumpyFeatures can only be created from flat arrays. Passed"
                f" input's shape: {len(data.shape)}"
            )
        if data.dtype.type is not np.string_:
            if data.dtype.type not in DTYPE_MAPPING:
                raise ValueError(
                    f"Unsupported dtype {data.dtype} for NumpyFeature."
                    f" Supported dtypes: {DTYPE_MAPPING.keys()}"
                )

        self.name = name
        self.data = data
        self.dtype = data.dtype.type

    def __repr__(self) -> str:
        return f"{self.name}: {self.data.__repr__()}"

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, NumpyFeature):
            return False

        if self.name != __o.name:
            return False

        if not np.array_equal(self.data, __o.data, equal_nan=True):
            return False

        return True

    def core_dtype(self) -> Any:
        if self.dtype.type is np.string_:
            return dtype.STRING
        return DTYPE_MAPPING[self.dtype]


class NumpyEvent:
    def __init__(
        self,
        data: Dict[Tuple, List[NumpyFeature]],
        sampling: NumpySampling,
    ) -> None:
        self.data = data
        self.sampling = sampling

    @property
    def first_index_level(self) -> Tuple:
        first_index_level = None
        try:
            first_index_level = next(iter(self.data))
        except StopIteration:
            return None

        return first_index_level

    @property
    def feature_count(self) -> int:
        if len(self.data.keys()) == 0:
            return 0

        return len(self.data[self.first_index_level])

    @property
    def feature_names(self) -> List[str]:
        if len(self.data.keys()) == 0:
            return []

        # Only look at the feature in the first index
        # to get the feature names. All features in all
        # indexes should have the same names
        return [feature.name for feature in self.data[self.first_index_level]]

    def schema(self) -> Event:
        return Event(
            features=[
                feature.schema() for feature in list(self.data.values())[0]
            ],
            sampling=self.sampling.names,
        )

    @staticmethod
    def from_dataframe(
        df: pd.DataFrame,
        index_names: List[str],
        timestamp_name: str = "timestamp",
    ) -> "NumpyEvent":
        """Function to convert a pandas DataFrame to a NumpyEvent

        Args:
            df: DataFrame to convert to NumpyEvent
            index_names: Names of the indexes of the DataFrame
            timestamp_name: Name for timestamp index. Defaults to "timestamp".

        Returns:
            NumpyEvent: NumpyEvent created from DataFrame

        Raises:
            ValueError: If index_names or timestamp_name are not in df columns

        Example:
            >>> import pandas as pd
            >>> from temporian.implementation.numpy.data.event import NumpyEvent
            >>> df = pd.DataFrame(
            ...     data=[
            ...         [666964, 1.0, 740.0],
            ...         [666964, 2.0, 508.0],
            ...         [574016, 3.0, 573.0],
            ...     ],
            ...     columns=["product_id", "timestamp", "costs"],
            ... )
            >>> event = NumpyEvent.from_dataframe(df, index_names=["product_id"])
            ]


        """
        # check index names and timestamp name are in df columns
        missing_columns = [
            column
            for column in index_names + [timestamp_name]
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing columns {missing_columns} in DataFrame. "
                f"Columns: {df.columns}"
            )

        # columns that are not indexes or timestamp
        feature_columns = [
            column
            for column in df.columns
            if column not in index_names + [timestamp_name]
        ]

        sampling = {}
        data = {}

        # The user provided an index
        if index_names:
            group_by_indexes = df.groupby(index_names)

            for group in group_by_indexes.groups:
                columns = group_by_indexes.get_group(group)
                timestamp = columns[timestamp_name].to_numpy()

                # Convert group to tuple, useful when its only one value
                if not isinstance(group, tuple):
                    group = (group,)

                sampling[group] = timestamp
                data[group] = [
                    NumpyFeature(feature, columns[feature].to_numpy())
                    for feature in feature_columns
                ]
        # The user did not provide an index
        else:
            timestamp = df[timestamp_name].to_numpy()
            sampling[()] = timestamp
            data[()] = [
                NumpyFeature(feature, df[feature].to_numpy())
                for feature in feature_columns
            ]

        numpy_sampling = NumpySampling(index=index_names, data=sampling)

        return NumpyEvent(data=data, sampling=numpy_sampling)

    def to_dataframe(self) -> pd.DataFrame:
        """Function to convert a NumpyEvent to a pandas DataFrame

        Returns:
        pd.DataFrame: DataFrame created from NumpyEvent
        """
        feature_names = self.feature_names
        index_names = self.sampling.index
        columns = index_names + feature_names + ["timestamp"]

        df = pd.DataFrame(data=[], columns=columns)

        # append every feature to the dataframe. without index
        for index, features in self.data.items():
            timestamps = self.sampling.data[index]

            for i, timestamp in enumerate(timestamps):
                # add row to dataframe
                row = (
                    list(index)
                    + [feature.data[i] for feature in features]
                    + [timestamp]
                )
                df.loc[len(df)] = row

        # Convert to original dtypes, can be more efficient
        first_index = self.first_index_level
        first_features = self.data[first_index]

        # get feature dtypes
        features_dtypes = {
            feature.name: feature.data[0].dtype for feature in first_features
        }

        # get tuple index dtypes
        index_dtypes = {
            index_name: type(first_index[i])
            for i, index_name in enumerate(self.sampling.index)
        }

        # get timestamp dtype
        first_timestamp = self.sampling.data[first_index][0]
        sampling_dtype = {"timestamp": first_timestamp.dtype}

        df = df.astype({**features_dtypes, **index_dtypes, **sampling_dtype})

        return df

    def __repr__(self) -> str:
        return self.data.__repr__() + " " + self.sampling.__repr__()

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, NumpyEvent):
            return False

        # Check equal sampling and index values
        if self.sampling != __o.sampling:
            return False

        # Check same features
        if self.feature_names != __o.feature_names:
            return False

        # Check each feature is equal in each index
        for index in self.data.keys():
            # Check both feature list are equal
            if self.data[index] != __o.data[index]:
                return False

        return True
