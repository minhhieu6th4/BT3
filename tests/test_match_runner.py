from judge.match_runner import MatchRunner


def test_match_runner_returns_result_object():
    runner = MatchRunner(
        "d:/BT3/bots/examples/greedy_bot.py",
        "d:/BT3/bots/examples/random_bot.py",
        max_turns=20,
    )

    result = runner.run_match()

    assert hasattr(result, "winner")
    assert hasattr(result, "reason")
    assert hasattr(result, "moves")
    assert result.winner in {1, 2, None}
    assert isinstance(result.reason, str)
    assert isinstance(result.moves, list)
