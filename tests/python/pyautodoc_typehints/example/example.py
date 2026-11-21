class A:
    def test(self, a: int) -> bool:
        """Test.

        Args:
            a: Argument
        """
        return False


class Series:
    """An ordered set of :attr:`values`.

    Attributes:
        values: The original values.
        dynamic (float): An attribute supplied at runtime.
    """

    def __init__(self):
        self.values: list[int] = []
        """One entry per row."""


class FilteredSeries(Series):
    """A subset of the original series.

    Attributes
    ----------
    values : sequence of positive integers
        The retained values.
    """
