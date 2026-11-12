from sklearn.model_selection import train_test_split

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer

if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(df, **kwargs):
    """
    Split the Iris dataset into 80% training
    data and 20% testing data.
    """
    output = df.copy()

    train_indices, test_indices = train_test_split(
        output.index,
        test_size=0.2,
        random_state=42,
        stratify=output["target"]
    )

    output["split"] = "train"
    output.loc[test_indices, "split"] = "test"

    return output


@test
def test_output(df):
    assert df is not None, "Prepared dataset is missing"
    assert (df["split"] == "train").sum() == 120
    assert (df["split"] == "test").sum() == 30