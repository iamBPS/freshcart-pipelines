from pathlib import Path
import pandas as pd

if 'data_exporter' not in globals():
    try:
        from mage_ai.data_preparation.decorators import data_exporter
    except ImportError:
        def data_exporter(func):
            return func

if 'test' not in globals():
    try:
        from mage_ai.data_preparation.decorators import test
    except ImportError:
        def test(func):
            return func


@data_exporter
def save_results(df, **kwargs):
    """Save model predictions to CSV."""

    filepath = Path.cwd() / "iris_predictions.csv"

    df.to_csv(filepath, index=False)

    print(f"Predictions saved to: {filepath}")
    print(f"Total predictions: {len(df)}")

    return str(filepath)


@test
def test_output(filepath):
    assert filepath is not None, "Output filepath is missing"

    path = Path(filepath)

    assert path.exists(), "iris_predictions.csv was not created"

    saved_data = pd.read_csv(path)

    assert len(saved_data) == 30, "Expected 30 saved predictions"
    assert "actual" in saved_data.columns
    assert "predicted" in saved_data.columns