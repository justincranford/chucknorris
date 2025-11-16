import io

import pytest

from quotes import generator

pytest.importorskip("pytest_benchmark")


def test_generate_quotes_benchmark(benchmark):
    db = "scraper/quotes.db"
    benchmark(lambda: generator.generate_quotes(db_path=db, count=100, seed=42))


def test_export_json_benchmark(benchmark):
    db = "scraper/quotes.db"
    quotes = generator.generate_quotes(db_path=db, count=100, seed=42)
    out = io.StringIO()
    benchmark(lambda: generator.export_quotes_json(quotes, out))
