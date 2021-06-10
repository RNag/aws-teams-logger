from typing import Tuple, Dict, Any, List

from .base_logger import _BaseLogger, _BulkBaseLogger
from ..constants import AWS_LOG_GROUP, AWS_REGION, SOURCE_CODE
from ..log import LOG
from ..models import TaskContext


class TaskLogger(_BaseLogger):
    """
    This class can be used to decorate ECS functions or methods, such as ones
    that will be run in a Fargate task. However this can also be used to
    decorate any generic functions or methods as well.

    See the documentation in the base class (:class:`_BaseLogger`) for more
    info.

    """
    SUBJECT_PREFIX = 'TASK FAILURE'

    FUNCTION_TYPE = 'Task'

    _task_metadata = None

    @classmethod
    def _set_task_metadata(cls):
        if cls._task_metadata is None:
            LOG.info('Retrieving ECS task metadata')
            cls._task_metadata = TaskContext.get_ecs_metadata()

    def _set_context(self, func, *args, **kwargs):
        self.context = TaskContext(func)
        self._set_task_metadata()

    def _get_context_and_links(self) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:

        context, links = {}, []
        aws_root = 'https://console.aws.amazon.com'
        aws_region = AWS_REGION

        cluster_name = None
        image_id = image = None
        log_group_name = AWS_LOG_GROUP
        logs_region_name = aws_region
        log_stream_name = None

        if self._task_metadata:
            container_labels = self._task_metadata.get('Labels', {})
            ecs_cluster_info = container_labels.get('com.amazonaws.ecs.cluster')
            log_options = self._task_metadata.get('LogOptions', {})
            image = self._task_metadata.get('Image')
            image_id = self._task_metadata.get('ImageID')

            if image:
                context['ECR Repo'] = image.split('/', 1)[-1].split(':', 1)[0]

            context['Function Name'] = self.context.function_name

            if ecs_cluster_info:
                ecs_cluster_parts = ecs_cluster_info.split(':')
                aws_region = ecs_cluster_parts[3]
                account_id = ecs_cluster_parts[4]
                account_name = self._get_account_name()
                cluster_name = ecs_cluster_parts[-1].split('/', 1)[-1]
                # Add account details to context
                context.update({'Account Name': account_name,
                                'Account Id': account_id})

            if log_options:
                log_group_name = log_options.get('awslogs-group')
                logs_region_name = log_options.get('awslogs-region')
                log_stream_name = log_options.get('awslogs-stream')

        else:
            context['Function Name'] = self.context.function_name

        if SOURCE_CODE:
            links.append({'location': SOURCE_CODE, 'text': 'Link to Source'})

        if cluster_name:
            links.append({
                'location': f'{aws_root}/ecs/home?region={aws_region}#/clusters/{cluster_name}',
                'text': 'Link to ECS Cluster'
            })
        else:
            links.append({
                'location': f'{aws_root}/ecs/home?region={aws_region}#/clusters',
                'text': 'Link to ECS'
            })

        if image and image_id:
            account_id = image.split('.', 1)[0]
            links.append({
                'location': f'{aws_root}/ecr/repositories/private/{account_id}/'
                            f'{context["ECR Repo"]}/image/{image_id}/details/'
                            f'?region={aws_region}',
                'text': 'Link to Image'
            })

        if log_group_name:
            if log_stream_name:
                location = (f'{aws_root}/cloudwatch/home?region={logs_region_name}'
                            f'#logEventViewer:group={log_group_name};stream={log_stream_name}')
            else:
                location = (f'{aws_root}/cloudwatch/home?region={logs_region_name}'
                            f'#logEventViewer:group={log_group_name}')

            links.append({
                'location': location,
                'text': 'Link to Logs'
            })

        return context, links


class BulkTaskLogger(TaskLogger, _BulkBaseLogger):
    """
    This class can be used to decorate ECS functions or methods, such as ones
    that will be run in a Fargate task. However this can also be used to
    decorate any generic functions or methods as well.

    The `Bulk` logger implementation will send templated emails in bulk,
    e.g. via the ``ses:SendBulkTemplatedEmail`` API call. Use this
    implementation when it is expected that multiple logs will be sent to Teams
    or Outlook, as there will be a performance increase when using a `Bulk`
    logger.

    See the documentation in the base class (:class:`_BaseLogger`) for more
    info.
    """
