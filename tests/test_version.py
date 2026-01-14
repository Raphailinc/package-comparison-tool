from package_comparison_tool.version import EVR, compare_evr, compare_version_release, rpmvercmp


def test_rpmvercmp_trailing_zeros_are_equal() -> None:
    assert rpmvercmp("1", "1.0") == 0
    assert rpmvercmp("1.0.0", "1") == 0


def test_rpmvercmp_alpha_suffix_is_prerelease() -> None:
    assert rpmvercmp("1", "1a") == 1
    assert rpmvercmp("1a", "1") == -1
    assert rpmvercmp("1", "1_beta") == 1
    assert rpmvercmp("1_beta", "1") == -1


def test_rpmvercmp_tilde_is_lowest() -> None:
    assert rpmvercmp("1.0~beta", "1.0") == -1
    assert rpmvercmp("1.0", "1.0~beta") == 1


def test_compare_version_release_examples() -> None:
    assert compare_version_release("6.1.7.1-alt1.2", "6.1.7.1-alt1.1") == 1
    assert compare_version_release("1.46.0-alt2", "1.46.0-alt1.p10.1") == 1


def test_compare_evr_respects_epoch() -> None:
    assert compare_evr(EVR(epoch=1, version="1.0", release="1"), EVR(epoch=0, version="9.0", release="1")) == 1

