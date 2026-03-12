MODELS_CSV = "data/models.csv"
EXPERIMENTS_CSV = "data/experiments.csv"
PREDICTIONS_CSV = "data/predictions.csv"
PRICES_CSV = "data/prices.csv"
DATA_REPORT_TXT = "data/data_report.txt"
RUN_DATA_DIR = "data"
MODELS_DIR = "models"
RUN_META_JSON = "metadata.json"
RUN_META_JSON_LEGACY = "meta.json"
MODEL_FIELDNAMES = [
    "name",
    "model_id",
    "generation",
    "task",
    "model_path",
    "training_size_days",
    "test_size_days",
    "parent_id",
    "reasoning",
    "log",
    "created_at_utc",
]
LINEAGE_GRAPH_JSON = "data/lineage_graph.json"
EXPERIMENT_FIELDNAMES = [
    "ticker",
    "from_date",
    "to_date",
    "model_id",
    "generation",
    "task",
    "status",
    "metrics",
    "started_at_utc",
    "finished_at_utc",
    "error",
]
PREDICTION_FIELDNAMES = ["ticker", "date", "model_id", "reasoning", "prediction", "actual", "is_correct", "created_at_utc"]
