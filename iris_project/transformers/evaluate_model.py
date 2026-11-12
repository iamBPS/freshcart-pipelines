import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.datasets import load_iris

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def evaluate_model(df, **kwargs):
    class_names = list(load_iris().target_names)
    labels = [0, 1, 2]

    actual = df["actual"].astype(int)
    predicted = df["predicted"].astype(int)

    matrix = confusion_matrix(actual, predicted, labels=labels)

    print("\nCONFUSION MATRIX")
    print("Classes:", class_names)
    print(matrix)

    report = classification_report(
        actual,
        predicted,
        labels=labels,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    rows = []

    for name in class_names + ["macro avg", "weighted avg"]:
        item = report[name]
        rows.append({
            "metric": name,
            "precision": item["precision"],
            "recall": item["recall"],
            "f1_score": item["f1-score"],
            "support": item["support"]
        })

    accuracy = report["accuracy"]
    rows.append({
        "metric": "overall accuracy",
        "precision": accuracy,
        "recall": accuracy,
        "f1_score": accuracy,
        "support": len(actual)
    })

    metrics_df = pd.DataFrame(rows)

    print("\nCLASSIFICATION METRICS")
    print(metrics_df.to_string(index=False))

    return metrics_df


@test
def test_evaluation(output, **kwargs):
    assert not output.empty, "Evaluation output is empty"
    assert "overall accuracy" in output["metric"].values
    accuracy = output.loc[
        output["metric"] == "overall accuracy", "precision"
    ].iloc[0]
    assert 0 <= accuracy <= 1, "Invalid accuracy value"