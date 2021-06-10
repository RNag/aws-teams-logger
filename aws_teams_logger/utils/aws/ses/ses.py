import os
from concurrent.futures import ThreadPoolExecutor
from json import dumps
from typing import Union, List, Dict, Any

from aws_teams_logger.log import LOG
from .models import BulkDestination
from ..client_cache import ClientCache
from ...decorators import log_time
from ...split import divide_chunks
from ...types import as_list


class SESHelper(ClientCache):

    SERVICE_NAME = 'ses'

    # There is a hard limit of 50 Destinations when making a call to the
    # `ses:SendBulkTemplatedEmail` API
    MAX_BULK_DESTINATIONS = 50

    @staticmethod
    def _op_is_success(response: Dict[str, Any]) -> bool:
        """Check if response indicates an operation was a success"""
        return response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200

    @log_time
    def send_templated_email(self, name: str,
                             data: Dict[str, Any],
                             to_addresses: Union[List[str], str],
                             from_address: str,
                             reply_to_addresses: Union[List[str], str]):
        """
        Send templated email via SES client
        """
        response = self.client.send_templated_email(
            Source=from_address,
            Destination={'ToAddresses': as_list(to_addresses)},
            ReplyToAddresses=as_list(reply_to_addresses),
            Template=name,
            TemplateData=dumps(data)
        )

        return response

    @log_time
    def send_bulk_templated_email(self, name: str,
                                  destinations: List[BulkDestination],
                                  from_address: str,
                                  reply_to_addresses: Union[List[str], str]):
        """
        Send a bulk templated email via SES client

        Ref: https://docs.aws.amazon.com/ses/latest/APIReference/API_SendBulkTemplatedEmail.html
        """
        if not destinations:
            return

        destination_list = [dest.dict for dest in destinations]

        if len(destination_list) > self.MAX_BULK_DESTINATIONS:
            # We have more than :attr:`MAX_BULK_DESTINATIONS` emails to send.
            #
            # AWS recommends dividing the recipient list into groups of 50 or
            # fewer, and calling the SendBulkTemplatedEmail operation several
            # times on each group.
            dest_chunks = list(divide_chunks(
                destination_list, self.MAX_BULK_DESTINATIONS))
            num_workers = min(10, len(dest_chunks))

            with ThreadPoolExecutor(max_workers=num_workers) as pool:
                for dest_chunk in dest_chunks:
                    pool.submit(self._call_bulk_templated_email,
                                name, dest_chunk,
                                from_address, reply_to_addresses)

        else:
            # We have fewer than :attr:`MAX_BULK_DESTINATIONS` emails - it can
            # be sent in a single API call.
            self._call_bulk_templated_email(
                name, destination_list, from_address, reply_to_addresses)

    def _call_bulk_templated_email(
            self, name: str, destination_list: List[Dict],
            from_address: str, reply_to_addresses: Union[List[str], str]):
        """Calls the underlying `ses:SendBulkTemplatedEmail` operation"""
        return self.client.send_bulk_templated_email(
            Source=from_address,
            Destinations=destination_list,
            ReplyToAddresses=as_list(reply_to_addresses),
            Template=name,
            DefaultTemplateData=dumps(destination_list[0])
        )

    def replace_template(self, template_data: Dict[str, Any]) -> bool:
        """
        Update or create an SES template
        """
        try:
            return self.update_template(template_data)

        except self.client.exceptions.TemplateDoesNotExistException:
            LOG.debug('%s: creating template, as it does not exist',
                      template_data['TemplateName'])
            return self.create_template(template_data)

        except self.client.exceptions.InvalidTemplateException as e:
            LOG.warning(e)
            return False

    @log_time
    def update_template(self, template_data: Dict[str, Any]) -> bool:
        """Update an SES template"""
        response = self.client.update_template(
            Template=template_data
        )

        return self._op_is_success(response)

    @log_time
    def create_template(self, template_data: Dict[str, Any]) -> bool:
        """Create a new SES template"""
        response = self.client.create_template(
            Template=template_data
        )

        return self._op_is_success(response)

    @log_time
    def delete_template(self, template_name: str) -> bool:
        """Delete an SES template"""

        response = self.client.delete_template(
            TemplateName=template_name
        )

        return self._op_is_success(response)

    @log_time
    def get_template(self, name: str) -> bool:
        """Get an SES template"""
        response = self.client.get_template(
            TemplateName=name
        )

        return response

    @log_time
    def test_render_template(self, name: str, data: Dict[str, Any],
                             html_file_name='email_body.html') -> bool:
        """
        Attempt to render an SES template using provided template arguments.

        The expected HTML body is rendered in a web browser which will
        automatically be opened.

        """
        import inspect
        import webbrowser

        # Skip Stack @index=1 as that leads to decorators.py
        caller_dir = os.path.dirname((inspect.stack()[2])[1])

        response = self.client.test_render_template(
            TemplateName=name,
            TemplateData=dumps(data)
        )

        render_data = response['RenderedTemplate'].replace('\r\n', '\n')

        header_data, html_data = render_data.split('\n\n', 1)
        LOG.info('Email Headers:\n%s', header_data)

        html_file_path = os.path.join(caller_dir, html_file_name)

        with open(html_file_path, 'w') as out_file:
            out_file.write(html_data)

        LOG.info(f'Wrote HTML file out to: %s', html_file_path)

        webbrowser.open_new_tab(f'file://{html_file_path}')

        return render_data
