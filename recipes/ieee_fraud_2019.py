import datatable as dt
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from h2oaicore.models import CustomModel, BaseCustomModel, LightGBMModel
from h2oaicore.transformer_utils import CustomTransformer
from h2oaicore.systemutils import config, physical_cores_count
import datetime


def get_datetime_from_transactionDT(X: dt.Frame):
    if "TransactionDT" not in X.names:
        return None

    if X[:, "TransactionDT"].ltypes[0] != dt.ltype.int:
        return None

    # This is the original integer feature
    startdate = datetime.datetime.strptime('2017-12-01', "%Y-%m-%d")
    return X[:, 'TransactionDT'].to_pandas()['TransactionDT'].apply(
        lambda x: (startdate + datetime.timedelta(seconds=x))
    )


class MyIEEEDateTimeTransformer(CustomTransformer):
    """
    Transforms TransactionDT feature to proper datetime and provides DAI with day, month ...
    """

    @property
    def display_name(self):
        return "IEEEDateTime"

    @staticmethod
    def get_default_properties():
        return dict(col_type="all", min_cols="all", max_cols="all", relative_importance=1)

    def fit_transform(self, X: dt.Frame, y: np.array = None):
        return self.transform(X)

    def transform(self, X: dt.Frame):
        # Make TransactionDT a DateTime
        ieee_datetime = get_datetime_from_transactionDT(X)
        if ieee_datetime is not None:
            output =  dt.Frame(
                ieee_dt_day=ieee_datetime.dt.day.values,
                ieee_dt_dayofweek = ieee_datetime.dt.dayofweek.values,
                ieee_dt_dayofyear = ieee_datetime.dt.dayofyear.values,
                ieee_dt_week = ieee_datetime.dt.week.values,
                ieee_dt_hour = ieee_datetime.dt.hour.values,
                ieee_dt_month=ieee_datetime.dt.month.values,
            )
            self._output_feature_names = list(output.names)
            self._feature_desc = list(output.names)

            return output

        else:
            return np.zeros(X.shape[0])


class MyIEEEGroupBysTransformers(CustomTransformer):

    def __init__(self, group_col, **kwargs):
        super().__init__(**kwargs)
        self.group_col = group_col

    @property
    def display_name(self):
        return "IEEEGroupBys_" + self.group_col

    @staticmethod
    def get_default_properties():
        return dict(col_type="all", min_cols="all", max_cols="all", relative_importance=1)

    @staticmethod
    def get_parameter_choices():
        return {"group_col": ['card1', 'card2', 'card3', 'card4']}

    def fit_transform(self, X: dt.Frame, y: np.array = None):

        return self.transform(X)

    def transform(self, X: dt.Frame):
        ieee_datetime = get_datetime_from_transactionDT(X)

        if (self.group_col in X.names) & (ieee_datetime is not None):

            X = dt.Frame(X[:, self.group_col])
            X[:, 'date'] = dt.Frame(ieee_datetime.dt.strftime('%Y%m%d').values)

            # Compute daily counts
            daily_cnt = X[:, {"daily_cnt": dt.count()}, dt.by("date")]
            daily_cnt.key = ["date"]
            X = X[:, :, dt.join(daily_cnt)]

            # Compute card count
            col_cnt = X[:, {"col_cnt": dt.count()}, dt.by(*["date", self.group_col])]
            col_cnt.key = ["date", self.group_col]
            X = X[:, :, dt.join(col_cnt)]

            self._output_feature_names = ["IEEEGroupBys_" + self.group_col]
            self._feature_desc = ["IEEEGroupBys_" + self.group_col]

            return X[:, dt.f["col_cnt"] / dt.f["daily_cnt"]]

        else:

            return np.zeros(X.shape[0])