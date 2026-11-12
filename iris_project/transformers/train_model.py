import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score

if 'transformer' not in globals():
    try:
        from mage_ai.data_preparation.decorators import transformer
    except ImportError:
        def transformer(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@transformer
def train_model(df, **kwargs):
    """Train a Decision Tree and generate predictions."""

    max_depth = int(kwargs.get("max_depth", 3))

    train_df = df[df["split"] == "train"]
    test_df = df[df["split"] == "test"]

    feature_columns = [
        col for col in df.columns
        if col not in ["target", "split"]
    ]

    X_train = train_df[feature_columns]
    y_train = train_df["target"]
    X_test = test_df[feature_columns]
    y_test = test_df["target"]

    model = DecisionTreeClassifier(
        max_depth=max_depth,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)

    print(f"Maximum tree depth: {max_depth}")
    print(f"Test accuracy: {accuracy:.4f}")

    results = pd.DataFrame({
        "row_index": test_df.index,
        "actual": y_test.to_numpy(),
        "predicted": predictions,
        "accuracy": [accuracy] * len(test_df),
        "max_depth": [max_depth] * len(test_df)
    })

    return results


@test
def test_accuracy(df):
    assert df is not None, "Model output is missing"
    assert len(df) == 30, "Expected 30 test predictions"

    accuracy = float(df["accuracy"].iloc[0])

    assert accuracy >= 0.80, (
        f"PROBLEM: Test accuracy {accuracy:.4f} is below 0.80"
    )