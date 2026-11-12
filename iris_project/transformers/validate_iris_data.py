if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer

if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def validate_iris_data(df, **kwargs):
    """
    Validate the Iris dataset before model preparation.
    """
    assert df is not None, "Iris dataset is missing"

    missing_values = int(df.isnull().sum().sum())
    class_count = int(df["target"].nunique())

    print("========== IRIS DATA QUALITY CHECK ==========")
    print(f"Total rows: {len(df)}")
    print(f"Missing values: {missing_values}")
    print(f"Number of classes: {class_count}")

    assert missing_values == 0, "Dataset contains missing values"
    assert class_count == 3, "Expected exactly three Iris classes"

    return df


@test
def test_iris_data_quality(df):
    assert df is not None
    assert len(df) == 150
    assert df.isnull().sum().sum() == 0
    assert df["target"].nunique() == 3