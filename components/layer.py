class Layer:

    @property
    def start_time(self):
        """Return the start time of this layer in hours (0–24)."""
        raise NotImplementedError("Layer must implement start_time.")

    @property
    def end_time(self):
        """Return the end time of this layer in hours (0–24)."""
        raise NotImplementedError("Layer must implement end_time.")

    def plot(self, ax, base):
        """
        Plot this layer using the given Axes and CalendarPlot context.
        :param ax: The Axes object for the plot.
        :param calendar: The CalendarPlot instance providing context.
        """
        raise NotImplementedError("Each layer must implement the plot method.")
    def footer(self, fig, footer_dimensions, base):
        """
        Render the footer for this layer onto the provided Axes object.
        Each layer is responsible for its unique footer layout.
        """
        raise NotImplementedError("Each layer must implement the footer method.")