import logging
from math import log
import stat
import uuid
from dash import dcc, html
from frozendict import frozendict

from purchasing_dashboard.layout.common.store import STORE_TO_DEPENDENTS


from purchasing_dashboard.utils.logging import logger


class TabContentContainerAIO(html.Div):
    """
    AIO Tab Content Container component.

    This component represents a container for tab content.
    It is designed to work with the AIO framework for building interactive web applications.
    """

    class ids:

        @staticmethod
        def loading_wrapper(aio_id):
            """
            ID for the dcc.Loading wrapper of the content.
            """
            return {
                "aio_id": aio_id,
                "component": "TabContentContainerAIO",
                "subcomponent": "tab-loading"
            }

        @staticmethod
        def time_dependency_store(aio_id):
            """
            ID for the time dependency store dcc.Store.
            """
            return {
                "aio_id": aio_id,
                "component": "TabContentContainerAIO",
                "subcomponent": "time-dependency-store"
            }

    ids = ids

    def __init__(self, aio_id, content, data_dependencies, has_time_bucket_dependency, target_components={}, *args, **kwargs):
        """
        Initializes the TabContentContainerAIO with the given parameters.

        :param aio_id: Unique identifier for the AIO component.
        :param content: The content to be displayed in the tab.
        :param data_names: List of data names that this component depends on.
        :param time_bucket_dependent: Boolean indicating if the content depends on the time bucket.
        :param args: Additional positional arguments.
        :param kwargs: Additional keyword arguments.
        """
        if aio_id is None:
            aio_id = str(uuid.uuid4())
        logger.debug(
            "Instantiating TabContentContainerAIO with aio_id: %s", aio_id)
        className = "tab-content-margin"

        own_id = frozendict(self.ids.loading_wrapper(aio_id))
        for dependency in data_dependencies:
            mapping = STORE_TO_DEPENDENTS.get(dependency, set())
            mapping.add(own_id)
            STORE_TO_DEPENDENTS[dependency] = mapping
            # logger.debug(
            #    "Mapping data dependency '%s' to dependents: %s",
            #    dependency, STORE_TO_DEPENDENTS[dependency])

        # Add the loading wrapper
        target_components[f"{aio_id}-loading-dummy-inner"] = "children"
        children = dcc.Loading(children=[
            content,
            dcc.Store(
                id=self.ids.time_dependency_store(aio_id),
                data=has_time_bucket_dependency
            ),
        ],
            target_components=target_components,
            id=self.ids.loading_wrapper(aio_id),
            parent_className=className,
            delay_show=100,
            delay_hide=250,
            overlay_style={"visibility": "visible", "filter": "blur(2px)"},
        )
        super().__init__(
            children=children,
            *args,
            **kwargs,
        )
