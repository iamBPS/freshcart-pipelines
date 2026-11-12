from sklearn.datasets import load_iris
from pandas import DataFrame

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader

if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_iris_data(**kwargs) -> DataFrame:
    """Load the Iris dataset as a pandas DataFrame."""
    return load_iris(as_frame=True).frame


@test
def test_output(df):
    assert df is not None, "Dataset output is missing"
    assert len(df) == 150, "Iris dataset must contain 150 rows"
    assert "target" in df.columns
    assert df["target"].nunique() == 3