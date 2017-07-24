from devicehive import DeviceException
from devicehive import ApiResponseException


def test_list(test):
    # TODO: add websocket support when API will be fixed.
    test.only_http_implementation()

    def handle_connect(handler):
        server_timestamp = handler.api.get_info()['server_timestamp']
        test_id = test.generate_id('list-commands')
        options = [{'command': '%s-name-1' % test_id, 'lifetime': 100,
                    'status': '1'},
                   {'command': '%s-name-2' % test_id, 'lifetime': 100,
                    'status': '2'}]
        device = handler.api.put_device(test_id)
        for option in options:
            device.send_command(option['command'], lifetime=option['lifetime'],
                                status=option['status'])
        command_0, command_1 = device.list_commands()
        # TODO add websocket tests after server response will be fixed.
        if test.http_transport():
            assert command_0.command() == options[1]['command']
            assert command_1.command() == options[0]['command']
        commands = device.list_commands(start=server_timestamp)
        # TODO add websocket tests after server response will be fixed.
        if test.http_transport():
            assert len(commands) == len(options)
        assert not device.list_commands(start=server_timestamp,
                                        end=server_timestamp)
        command_name = options[0]['command']
        command, = device.list_commands(command=command_name)
        assert command.command() == command_name
        status = options[0]['status']
        command, = device.list_commands(status=status)
        assert command.status == status
        command_0, command_1 = device.list_commands(sort_field='command',
                                                    sort_order='ASC')
        assert command_0.command() == options[0]['command']
        assert command_1.command() == options[1]['command']
        command_0, command_1 = device.list_commands(sort_field='command',
                                                    sort_order='DESC')
        assert command_0.command() == options[1]['command']
        assert command_1.command() == options[0]['command']
        command, = device.list_commands(sort_field='command', sort_order='ASC',
                                        take=1)
        assert command.command() == options[0]['command']
        command, = device.list_commands(sort_field='command', sort_order='ASC',
                                        take=1, skip=1)
        assert command.command() == options[1]['command']
        device_1 = handler.api.get_device(test_id)
        device.remove()
        try:
            device.list_commands()
            assert False
        except DeviceException:
            pass
        try:
            device_1.list_commands()
            assert False
        except ApiResponseException as api_response_exception:
            # TODO: uncomment after server response will be fixed.
            # assert api_response_exception.code() == 404
            pass

    test.run(handle_connect)


def test_send(test):

    def handle_connect(handler):
        device_id = test.generate_id('send-command')
        command_name = test.generate_id('send-command')
        device = handler.api.put_device(device_id)
        command = device.send_command(command_name)
        assert command.device_id() == device_id
        assert isinstance(command.id(), int)
        assert isinstance(command.user_id(), int)
        assert command.command() == command_name
        assert not command.parameters()
        assert not command.lifetime()
        assert command.timestamp()
        assert not command.status
        assert not command.result
        command_name = test.generate_id('send-command')
        parameters = 'parameters'
        lifetime = 10
        status = 'status'
        result = {'key': 'value'}
        command = device.send_command(command_name, parameters=parameters,
                                      lifetime=lifetime, status=status,
                                      result=result)
        assert command.device_id() == device_id
        assert isinstance(command.id(), int)
        assert isinstance(command.user_id(), int)
        assert command.command() == command_name
        assert command.parameters() == parameters
        assert command.lifetime() == lifetime
        assert command.timestamp()
        assert command.status == status
        assert command.result == result
        device_1 = handler.api.get_device(device_id)
        device.remove()
        try:
            device.send_command(command_name)
            assert False
        except DeviceException:
            pass
        try:
            device_1.send_command(command_name)
            assert False
        except ApiResponseException as api_response_exception:
            # TODO: uncomment after server response will be fixed.
            # assert api_response_exception.code() == 404
            pass

    test.run(handle_connect)


def test_save(test):

    def handle_connect(handler):
        device_id = test.generate_id('save-command')
        command_name = test.generate_id('save-command')
        device = handler.api.put_device(device_id)
        command = device.send_command(command_name)
        status = 'status'
        result = {'key': 'value'}
        command.status = status
        command.result = result
        command.save()
        device.remove()
        try:
            command.save()
            assert False
        except ApiResponseException as api_response_exception:
            # TODO: uncomment after server response will be fixed.
            # assert api_response_exception.code() == 404
            pass

    test.run(handle_connect)
