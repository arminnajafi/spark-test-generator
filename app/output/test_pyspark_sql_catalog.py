import pytest
from pyspark.sql import SparkSession

# Initialize a Spark session
spark = (
    SparkSession.builder.appName("pytest-spark-catalog").master("local").getOrCreate()
)


@pytest.fixture(scope="module")
def catalog():
    return spark.catalog


def test_current_database(catalog):
    # Check that the default database is 'default'
    assert catalog.currentDatabase() == "default"


def test_create_and_drop_temp_view(catalog):
    # Create a DataFrame
    df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])

    # Create a temporary view
    df.createOrReplaceTempView("people_view")

    # Check if the table exists
    assert catalog.tableExists("people_view") is True

    # Drop the temporary view
    catalog.dropTempView("people_view")

    # Ensure the table no longer exists
    assert catalog.tableExists("people_view") is False


def test_cache_and_uncache_table(catalog):
    # Create a DataFrame
    df = spark.createDataFrame([(1, "Alice"), (2, "Bob")], ["id", "name"])

    # Create a temporary view
    df.createOrReplaceTempView("people_cache")

    # Cache the table
    catalog.cacheTable("people_cache")

    # Check if the table is cached
    assert catalog.isCached("people_cache") is True

    # Uncache the table
    catalog.uncacheTable("people_cache")

    # Ensure the table is no longer cached
    assert catalog.isCached("people_cache") is False


def test_list_databases(catalog):
    # List all databases
    databases = catalog.listDatabases()

    # Verify the default database is in the list
    assert any(db.name == "default" for db in databases)
