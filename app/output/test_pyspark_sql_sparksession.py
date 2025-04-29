import pytest
from pyspark.sql import SparkSession, DataFrame, Row

# Initialize a SparkSession for use in tests
spark = (
    SparkSession.builder.master("local")
    .appName("PyTest SparkSession")
    .config("spark.some.config.option", "some-value")
    .getOrCreate()
)


def test_create_dataframe():
    # Test creating a DataFrame from a list of tuples
    data = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
    df: DataFrame = spark.createDataFrame(data, ["id", "name"])

    # Verify the schema
    assert df.schema.fieldNames() == ["id", "name"]

    # Verify the data
    result = df.collect()
    expected = [
        Row(id=1, name="Alice"),
        Row(id=2, name="Bob"),
        Row(id=3, name="Charlie"),
    ]
    assert result == expected


def test_sql_query():
    # Test executing an SQL query
    data = [(1, "Alice"), (2, "Bob"), (3, "Charlie")]
    df: DataFrame = spark.createDataFrame(data, ["id", "name"])
    df.createOrReplaceTempView("people")

    # noinspection SqlNoDataSourceInspection
    result = spark.sql("SELECT id, name FROM people WHERE id = 1").collect()
    expected = [Row(id=1, name="Alice")]
    assert result == expected


def test_range_function():
    # Test the range function
    df: DataFrame = spark.range(1, 4)

    # Verify the schema
    assert df.schema.fieldNames() == ["id"]

    # Verify the data
    result = df.collect()
    expected = [Row(id=1), Row(id=2), Row(id=3)]
    assert result == expected


# Stop the Spark session after tests
def teardown_module():
    spark.stop()


if __name__ == "__main__":
    pytest.main([__file__])
