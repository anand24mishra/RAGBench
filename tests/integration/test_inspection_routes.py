from tests.integration.test_api import make_client


def test_inspection_routes() -> None:
    client, _ = make_client()
    with client:
        # Evaluation routes
        res_base = client.get("/evaluation/baseline")
        assert res_base.status_code == 200
        data_base = res_base.json()
        assert data_base["metrics"]["mrr"] == 0.925
        assert data_base["metrics"]["recall_at_5"] == 1.0

        res_gen = client.get("/evaluation/generation-baseline")
        assert res_gen.status_code == 200
        data_gen = res_gen.json()
        assert "queries" in data_gen

        res_reg = client.get("/evaluation/regression")
        assert res_reg.status_code == 200
        assert res_reg.json()["status"] in {"pass", "fail", "inconclusive"}

        # Experiments routes
        res_exp = client.get("/experiments")
        assert res_exp.status_code == 200
        exps = res_exp.json()
        assert len(exps) >= 8
        assert any(e["id"] == "chunk-400-50" for e in exps)

        res_single = client.get("/experiments/chunk-400-50")
        assert res_single.status_code == 200
        assert res_single.json()["metrics"]["mrr"] == 0.95

        res_comp = client.get("/experiments/chunk-400-50/comparison")
        assert res_comp.status_code == 200
        assert "baseline_experiment_id" in res_comp.json()

        # Query inspection route
        res_inspect = client.get("/inspect/q001")
        assert res_inspect.status_code == 200
        assert res_inspect.json()["query_id"] == "q001"

        # System config route
        res_cfg = client.get("/system/config")
        assert res_cfg.status_code == 200
        assert res_cfg.json()["configuration"]["vector_store"] == "qdrant"
