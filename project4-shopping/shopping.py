import csv
import sys

from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

TEST_SIZE = 0.4


def main():

    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python shopping.py data")

    # Load data from spreadsheet and split into train and test sets
    evidence, labels = load_data(sys.argv[1])
    X_train, X_test, y_train, y_test = train_test_split(
        evidence, labels, test_size=TEST_SIZE
    )

    # Train model and make predictions
    model = train_model(X_train, y_train)
    predictions = model.predict(X_test)
    sensitivity, specificity = evaluate(y_test, predictions)

    # Print results
    print(f"Correct: {(y_test == predictions).sum()}")
    print(f"Incorrect: {(y_test != predictions).sum()}")
    print(f"True Positive Rate: {100 * sensitivity:.2f}%")
    print(f"True Negative Rate: {100 * specificity:.2f}%")


def load_data(filename):
    """
    Load shopping data from a CSV file `filename` and convert into a list of
    evidence lists and a list of labels. Return a tuple (evidence, labels).

    evidence should be a list of lists, where each list contains the
    following values, in order:
        - Administrative, an integer
        - Administrative_Duration, a floating point number
        - Informational, an integer
        - Informational_Duration, a floating point number
        - ProductRelated, an integer
        - ProductRelated_Duration, a floating point number
        - BounceRates, a floating point number
        - ExitRates, a floating point number
        - PageValues, a floating point number
        - SpecialDay, a floating point number
        - Month, an index from 0 (January) to 11 (December)
        - OperatingSystems, an integer
        - Browser, an integer
        - Region, an integer
        - TrafficType, an integer
        - VisitorType, an integer 0 (not returning) or 1 (returning)
        - Weekend, an integer 0 (if false) or 1 (if true)

    labels should be the corresponding list of labels, where each label
    is 1 if Revenue is true, and 0 otherwise.
    """
    import pandas as pd

    data = pd.read_csv(filename, dtype=str)

    int_columns = [
        'Administrative', 'Informational', 'ProductRelated', 
        'OperatingSystems', 'Browser', 'Region', 'TrafficType'
    ]

    float_columns = [
        'Administrative_Duration', 'Informational_Duration',
        'ProductRelated_Duration', 'BounceRates',
        'ExitRates', 'PageValues', 'SpecialDay'
    ]

    data[int_columns] = data[int_columns].astype(int)
    data[float_columns] = data[float_columns].astype(float)

    data['Revenue'] = data['Revenue'].map({
        'TRUE': 1,
        'FALSE': 0,
    }).astype(int)

    month_order = ['Jan', 'Feb', 'Mar', 'Apr',
                   'May', 'June', 'Jul', 'Aug',
                   'Sep', 'Oct', 'Nov', 'Dec']
    data['Month'] = data['Month'].map(
        lambda month: month_order.index(month)
    ).astype(int)

    data['VisitorType'] = data['VisitorType'].map(
        lambda x: 1 if x == 'Returning_Visitor' else 0
    ).astype(int)

    data['Weekend'] = data['Weekend'].map({
        'TRUE': 1,
        'FALSE': 0,
    }).astype(int)

    evidence_columns = [
        'Administrative',
        'Administrative_Duration',
        'Informational',
        'Informational_Duration',
        'ProductRelated',
        'ProductRelated_Duration',
        'BounceRates',
        'ExitRates',
        'PageValues',
        'SpecialDay',
        'Month',
        'OperatingSystems',
        'Browser',
        'Region',
        'TrafficType',
        'VisitorType',
        'Weekend',
    ]

    evidence = [
        list(row)
        for row in data[evidence_columns].itertuples(index=False, name=None)
    ]

    labels = data['Revenue'].tolist()

    return evidence, labels


def train_model(evidence, labels):
    """
    Given a list of evidence lists and a list of labels, return a
    fitted k-nearest neighbor model (k=1) trained on the data.
    """
    model = KNeighborsClassifier(n_neighbors=1)
    model.fit(X=evidence, y=labels)
    return model


def evaluate(labels, predictions):
    """
    Given a list of actual labels and a list of predicted labels,
    return a tuple (sensitivity, specificity).

    Assume each label is either a 1 (positive) or 0 (negative).

    `sensitivity` should be a floating-point value from 0 to 1
    representing the "true positive rate": the proportion of
    actual positive labels that were accurately identified.

    `specificity` should be a floating-point value from 0 to 1
    representing the "true negative rate": the proportion of
    actual negative labels that were accurately identified.
    """
    positive_count = 0
    negative_count = 0
    true_positive_count = 0
    true_negative_count = 0

    for label, prediction in zip(labels, predictions):
        if label == 1:
            positive_count += 1
            if prediction == 1:
                true_positive_count += 1
        else:
            negative_count += 1
            if prediction == 0:
                true_negative_count += 1
    
    sensitivity = 1.0 * true_positive_count / positive_count
    specificity = 1.0 * true_negative_count / negative_count

    return sensitivity, specificity


if __name__ == "__main__":
    main()
