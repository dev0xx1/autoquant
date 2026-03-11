MODELS_CSV = "data/models.csv"
EXPERIMENTS_CSV = "data/experiments.csv"
PREDICTIONS_CSV = "data/predictions.csv"
NEWS_CSV = "data/news.csv"
PRICES_CSV = "data/prices.csv"
DATA_REPORT_TXT = "data/data_report.txt"
RUNS_ROOT = "Documents/autoquant/runs"
RUN_DATA_DIR = "data"
RUN_SETTINGS_JSON = "settings.json"
MODELS_DIR = "models"
RUN_META_JSON = "meta.json"
MODEL_FIELDNAMES = ["model_id", "generation", "model_path", "parent_id", "reasoning", "log", "created_at_utc"]
LINEAGE_GRAPH_JSON = "data/lineage_graph.json"
EXPERIMENT_FIELDNAMES = [
    "ticker",
    "from_date",
    "to_date",
    "model_id",
    "generation",
    "status",
    "n_samples",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "weighted_f1",
    "macro_f1",
    "y_dist",
    "started_at_utc",
    "finished_at_utc",
    "error",
]
PREDICTION_FIELDNAMES = ["ticker", "date", "model_id", "reasoning", "prediction", "actual", "is_correct", "created_at_utc"]
