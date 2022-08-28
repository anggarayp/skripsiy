import 'package:drone_map2/data.dart';
import 'package:flutter/material.dart';
import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bluetooth_serial/flutter_bluetooth_serial.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:permission/permission.dart';
import 'dart:convert' show utf8;
import 'notifiers.dart';
import 'dart:convert';
import 'dart:typed_data';

void main() {
  runApp(MultiProvider(
    providers: [
      ChangeNotifierProvider<SingleNotifier>(
        create: (_) => SingleNotifier(),
      )
    ],
    child: MyApp(),
  ));
  print('Hello World');
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Drone Map',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        primaryColor: Colors.white,
      ),
      home: MapScreen(),
    );
  }
}

class MapScreen extends StatefulWidget {
  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  PermissionName permissionName = PermissionName.Location;

  BluetoothState _bluetoothState = BluetoothState.UNKNOWN;

  FlutterBluetoothSerial _bluetooth = FlutterBluetoothSerial.instance;

  BluetoothConnection connection;

  bool get isConnected => connection != null && connection.isConnected;

  String selectedProgram;

  final _formKey = GlobalKey<FormState>();
  TextEditingController destCoordinate1 = TextEditingController();
  TextEditingController destCoordinate2 = TextEditingController();
  TextEditingController destCoordinate3 = TextEditingController();
  TextEditingController destCoordinate4 = TextEditingController();

  @override
  void initState() {
    super.initState();

    FlutterBluetoothSerial.instance.state.then((state) {
      setState(() {
        _bluetoothState = state;
      });
    });

    enableBluetooth();

    FlutterBluetoothSerial.instance
        .onStateChanged()
        .listen((BluetoothState state) {
      setState(() {
        _bluetoothState = state;

        getPairedDevices();
      });
    });
  }

  Future<void> enableBluetooth() async {
    _bluetoothState = await FlutterBluetoothSerial.instance.state;

    if (_bluetoothState == BluetoothState.STATE_OFF) {
      await FlutterBluetoothSerial.instance.requestEnable();
      await getPairedDevices();
      return true;
    } else {
      await getPairedDevices();
    }
    return false;
  }

  List<BluetoothDevice> _devicesList = [];

  Future<void> getPairedDevices() async {
    List<BluetoothDevice> devices = [];

    try {
      devices = await _bluetooth.getBondedDevices();
    } on PlatformException {
      print("Error");
    }

    if (!mounted) {
      return;
    }

    setState(() {
      _devicesList = devices;
    });
  }

  bool isDisconnecting = false;
  bool _connected = false;
  bool _isButtonUnavailable = false;
  bool _coordinateSent = false;
  bool _dronefly = false;

  BluetoothDevice _device;
  static const _initialCameraPosition = CameraPosition(
    target: LatLng(-7.279918888894614, 112.79744026679379),
    zoom: 16.5,
  );

  GoogleMapController _googleMapController;
  Marker _origin;
  Marker _destination;
  Marker _destination2;
  Marker _destination3;
  Marker _destination4;

  @override
  void dispose() {
    _googleMapController.dispose();

    if (isConnected) {
      isDisconnecting = true;
      connection.dispose();
      connection = null;
    }

    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        centerTitle: false,
        title: const Text('Drone Map'),
        actions: [
          TextButton(
            onPressed: () => _getdronelocation(),
            style: TextButton.styleFrom(
                primary: Colors.green,
                textStyle: const TextStyle(fontWeight: FontWeight.w600)),
            child: const Text('Get drone location'),
          ),
          IconButton(
            icon: Icon(Icons.info_outline_rounded),
            onPressed: () => createAllertDialog(context),
          ),
        ],
      ),
      body: Center(
          child: Column(children: <Widget>[
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: <Widget>[
            Container(
              padding: EdgeInsets.only(left: 10.0),
              child: Text("Enable Bluetooth"),
            ),
            Container(
              padding: EdgeInsets.only(right: 10.0),
              child: Switch(
                value: _bluetoothState.isEnabled,
                onChanged: (bool value) {
                  future() async {
                    if (value) {
                      await FlutterBluetoothSerial.instance.requestEnable();
                    } else {
                      await FlutterBluetoothSerial.instance.requestDisable();
                    }

                    await getPairedDevices();
                    _isButtonUnavailable = false;

                    if (_connected) {
                      _disconnect();
                    }
                  }

                  future().then((_) {
                    setState(() {});
                  });
                },
              ),
            ),
          ],
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: <Widget>[
            Container(
              margin: EdgeInsets.only(left: 10.0),
              child: Text("Device List"),
            ),
            Container(
              margin: EdgeInsets.only(left: 10.0),
              width: MediaQuery.of(context).size.width * 0.4,
              child: DropdownButton(
                isExpanded: true,
                items: _getDeviceItems(),
                onChanged: (value) => setState(() => _device = value),
                value: _devicesList.isNotEmpty ? _device : null,
              ),
            ),
            Container(
              margin: EdgeInsets.only(right: 10.0),
              child: ElevatedButton(
                onPressed: _isButtonUnavailable
                    ? null
                    : _connected
                        ? _disconnect
                        : _connect,
                child: Text(_connected ? 'Disconnect' : 'Connect'),
              ),
            )
          ],
        ),
        Expanded(
          child: Container(
              padding: EdgeInsets.all(10.0),
              child: SizedBox(
                child: GoogleMap(
                  myLocationButtonEnabled: true,
                  zoomControlsEnabled: true,
                  initialCameraPosition: _initialCameraPosition,
                  onMapCreated: (GoogleMapController controller) =>
                      _googleMapController = controller,
                  markers: {
                    if (_origin != null) _origin,
                    if (_destination != null) _destination,
                    if (_destination2 != null) _destination2,
                    if (_destination3 != null) _destination3,
                    if (_destination4 != null) _destination4
                  },
                  onLongPress: _addMarker,
                ),
              )),
        ),
      ])),
      floatingActionButton: FloatingActionButton(
        backgroundColor: Theme.of(context).primaryColor,
        foregroundColor: Colors.black,
        onPressed: () => _googleMapController.animateCamera(
          CameraUpdate.newCameraPosition(_initialCameraPosition),
        ),
        child: const Icon(Icons.center_focus_strong),
      ),
      floatingActionButtonLocation: FloatingActionButtonLocation.startFloat,
      bottomNavigationBar: BottomAppBar(
        shape: const CircularNotchedRectangle(),
        child: IconTheme(
          data: IconThemeData(color: Theme.of(context).colorScheme.onPrimary),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: <Widget>[
              Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  IconButton(
                    icon: const Icon(Icons.add_location_alt_outlined,
                        color: Colors.black),
                    onPressed: () {
                      _origin != null
                          ? _addDestinationCoordinate(context)
                          : ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text(
                                    'No origin point selected. Please add origin of the drone.'),
                              ),
                            );
                    },
                  ),
                  Text('Destination'),
                ],
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  IconButton(
                    icon: const Icon(Icons.location_on, color: Colors.black),
                    onPressed: () {
                      _connected
                          ? _sendCoordinates()
                          : ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('No device selected'),
                              ),
                            );
                    },
                  ),
                  Text('Send')
                ],
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  IconButton(
                      icon: const Icon(Icons.computer_rounded,
                          color: Colors.black),
                      onPressed: () => _showSingleChoiceDialog(context)),
                  Text('Select')
                ],
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  IconButton(
                    icon: const Icon(Icons.airplanemode_active,
                        color: Colors.black),
                    onPressed: () {

                      _coordinateSent
                          ? _sendFlyCommand()
                          : ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('No coordinates sent'),
                              ),
                            );
                    },
                  ),
                  Text('Fly')
                ],
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: <Widget>[
                  IconButton(
                    icon: const Icon(Icons.flight_land, color: Colors.black),
                    onPressed: () {

                      _dronefly
                          ? _sendLandCommand()
                          : ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Drone still in the ground'),
                              ),
                            );
                    },
                  ),
                  Text('Land')
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _addMarker(LatLng pos) async {
    if (selectedProgram == 'Anfasa - Fire Detection') {
      if (_origin == null ||
          (_origin != null &&
              _destination != null &&
              _destination2 != null &&
              _destination3 != null &&
              _destination4 != null)) {
        setState(() {
          _origin = Marker(
            markerId: const MarkerId('origin'),
            infoWindow:
                InfoWindow(title: 'Origin (${pos.latitude}, ${pos.longitude})'),
            icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueGreen),
            position: pos,
          );

          _destination = null;
          _destination2 = null;
          _destination3 = null;
          _destination4 = null;
        });

        print('Origin: ${_origin.position}');
      } else if (_destination == null) {
        setState(() {
          _destination = Marker(
            markerId: const MarkerId('destination'),
            infoWindow: InfoWindow(
                title: 'Destination (${pos.latitude}, ${pos.longitude})'),
            icon:
                BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
            position: pos,
          );
        });
        print('Destination: ${_destination.position}');
      } else if (_destination2 == null) {
        setState(() {
          _destination2 = Marker(
            markerId: const MarkerId('destination2'),
            infoWindow: InfoWindow(
                title: 'Destination2 (${pos.latitude}, ${pos.longitude})'),
            icon:
                BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
            position: pos,
          );
        });
        print('Destination2: ${_destination2.position}');
      } else if (_destination3 == null) {
        setState(() {
          _destination3 = Marker(
            markerId: const MarkerId('destination3'),
            infoWindow: InfoWindow(
                title: 'Destination3 (${pos.latitude}, ${pos.longitude})'),
            icon:
                BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
            position: pos,
          );
        });
        print('Destination3: ${_destination3.position}');
      } else if (_destination4 == null) {
        setState(() {
          _destination4 = Marker(
            markerId: const MarkerId('destination4'),
            infoWindow: InfoWindow(
                title: 'Destination4 (${pos.latitude}, ${pos.longitude})'),
            icon:
                BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
            position: pos,
          );
        });
        print('Destination4: ${_destination4.position}');
      }
    } else {
      if (_origin == null || (_origin != null && _destination != null)) {
        setState(() {
          _origin = Marker(
            markerId: const MarkerId('origin'),
            infoWindow:
                InfoWindow(title: 'Origin (${pos.latitude}, ${pos.longitude})'),
            icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueGreen),
            position: pos,
          );

          _destination = null;
          _destination2 = null;
          _destination3 = null;
          _destination4 = null;
        });

        print('Origin: ${_origin.position}');
      } else if (_destination == null) {
        setState(() {
          _destination = Marker(
            markerId: const MarkerId('destination'),
            infoWindow: InfoWindow(
                title: 'Destination (${pos.latitude}, ${pos.longitude})'),
            icon:
                BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueBlue),
            position: pos,
          );
        });
        print('Destination: ${_destination.position}');
      }
    }
  }

  List<DropdownMenuItem<BluetoothDevice>> _getDeviceItems() {
    List<DropdownMenuItem<BluetoothDevice>> items = [];
    if (_devicesList.isEmpty) {
      items.add(DropdownMenuItem(
        child: Text('NONE'),
      ));
    } else {
      _devicesList.forEach((device) {
        items.add(DropdownMenuItem(
          child: Text(device.name),
          value: device,
        ));
      });
    }
    return items;
  }

  void _connect() async {
    if (_device == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('No device selected'),
        ),
      );
    } else {
      print(_device.address);
      if (!isConnected) {
        try {
          connection = await BluetoothConnection.toAddress(_device.address);
          print('Connected to the device');

          setState(() {
            _connected = true;
          });
        } catch (e) {
          if (!connection.isConnected) {
            setState(() {
              _connected = false;
            });
          }
          print(e);
        }
      }
    }
  }

  void _disconnect() async {
    await connection.close();
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
      content: Text('Device disconnected'),
    ));
    print('Device disconnected');

    if (!connection.isConnected) {
      setState(() {
        _connected = false;
      });
    }
  }

  void _sendCoordinates() async {
    if (selectedProgram == 'Anfasa - Fire Detection') {
      if (_origin != null &&
          _destination != null &&
          _destination2 != null &&
          _destination3 != null &&
          _destination4 != null) {
        connection.output.add(utf8.encode(
            'save ${_origin.position.latitude} ${_origin.position.longitude} ${_destination.position.latitude} ${_destination.position.longitude} ${_destination2.position.latitude} ${_destination2.position.longitude} ${_destination3.position.latitude} ${_destination3.position.longitude} ${_destination4.position.latitude} ${_destination4.position.longitude}'));

        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Coordinate sent'),
        ));

        _coordinateSent = true;

        print('Coordinate sent');
      } else if (_origin == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No origin selected'),
        ));
      } else if (_destination == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No destination selected'),
        ));
      } else if (_destination2 == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No destination2 selected'),
        ));
      } else if (_destination3 == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No destination3 selected'),
        ));
      } else if (_destination4 == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No destination4 selected'),
        ));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No coordinates selected'),
        ));
      }
    } else {
      if (_origin != null && _destination != null) {
        connection.output.add(utf8.encode(
            'save ${_origin.position.latitude} ${_origin.position.longitude} ${_destination.position.latitude} ${_destination.position.longitude}'));

        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Coordinate sent'),
        ));

        _coordinateSent = true;

        print('Coordinate sent');
      } else if (_origin == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No origin selected'),
        ));
      } else if (_destination == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No destination selected'),
        ));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('No coordinates selected'),
        ));
      }
    }
  }

  Future<dynamic> createAllertDialog(BuildContext context) {
    return showDialog(
        context: context,
        builder: (context) {
          return AlertDialog(
              title: Text("User Manual"),
              content: Text("AKTIVASI BLUTOOTH"
                  '\n'
                  "- aktifkan blutooth"
                  '\n'
                  "- pilih nama blutooth raspberry pi pada dropdown device list"
                  "- klik Connect"
                  '\n'
                  '\n'
                  "*jika nama blutooth raspberry pi tidak ada dalam device list, silahkan pairing manual dengan aplikasi blutooth"
                  '\n'
                  '\n'
                  "SET LOKASI AWAL DAN TUJUAN"
                  '\n'
                  "- pilih koordinat awal pada peta dengan cara menekan lama di peta pada titik yang akan dijadikan titik awal"
                  '\n'
                  "- pilih koordinat tujuan pada peta dengan cara menekan lama di peta pada titik yang akan dijadikan titik tujuan"
                  '\n'
                  "- klik Send Coordinates"
                  '\n'
                  "- Klik Fly"
                  '\n'
                  '\n'
                  "*Cek lokasi awal dengan cara klik tombol Origin yang berada pada atas layar"
                  '\n'
                  "*Cek lokasi tujuan dengan cara klik tombol Dest yang berada pada atas layar"),
              actions: <Widget>[
                MaterialButton(
                  elevation: 5.0,
                  child: Text('Close'),
                  onPressed: () {
                    Navigator.of(context).pop();
                  },
                )
              ]);
        });
  }

  _showSingleChoiceDialog(BuildContext context) => showDialog(
      context: context,
      builder: (context) {
        final _singleNotifier = Provider.of<SingleNotifier>(context);
        return AlertDialog(
          title: Text('Select Program to Run'),
          content: SingleChildScrollView(
            child: Container(
              width: double.infinity,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: programs
                    .map((e) => RadioListTile(
                          title: Text(e),
                          value: e,
                          groupValue: _singleNotifier.currentProgram,
                          selected: _singleNotifier.currentProgram == e,
                          onChanged: (value) {
                            _singleNotifier.updateProgram(value);
                            Navigator.of(context).pop();
                            selectedProgram = value;
                          },
                        ))
                    .toList(),
              ),
            ),
          ),
        );
      });

  void _sendFlyCommand() async {
    if (selectedProgram == 'Test Fly 3 Second') {
      connection.output.add(utf8.encode('test fly'));
    }
    if (selectedProgram == 'Test Fly Adit') {
      connection.output.add(utf8.encode('test fly-adit'));
    }
    if (selectedProgram == 'Clement - Automatic Landing - Red') {
      connection.output.add(utf8.encode('fly clement red'));
    }
    if (selectedProgram == 'Clement - Automatic Landing - Green') {
      connection.output.add(utf8.encode('fly clement green'));
    }
    if (selectedProgram == 'Clement - Automatic Landing - Blue') {
      connection.output.add(utf8.encode('fly clement blue'));
    }
    if (selectedProgram == 'Angga - Automatic Drone Delivery') {
      connection.output.add(utf8.encode('fly angga'));
    }
    if (selectedProgram == 'Rozak - Object and Color Detection') {
      connection.output.add(utf8.encode('fly rozak'));
    }
    if (selectedProgram == 'Denta - Face Tracking') {
      connection.output.add(utf8.encode('fly denta'));
    }
    if (selectedProgram == 'Anfasa - Fire Detection') {
      connection.output.add(utf8.encode('fly anfasa'));
      _getfirelocation();
    }

    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
      content: Text('Fly command sent'),
    ));

    _dronefly = true;
    _coordinateSent = false;

    print('Fly command sent');
  }

  void _sendLandCommand() async {
    if (selectedProgram == 'Test Fly 3 Second') {
      connection.output.add(utf8.encode('test fly'));
    }
    if (selectedProgram == 'Test Fly Adit') {
      connection.output.add(utf8.encode('test fly-adit'));
    }
    if (selectedProgram == 'Clement - Automatic Landing - Red' ||
        selectedProgram == 'Clement - Automatic Landing - Green' ||
        selectedProgram == 'Clement - Automatic Landing - Blue') {
      connection.output.add(utf8.encode('landing clement'));
    }
    if (selectedProgram == 'Angga - Automatic Drone Delivery') {
      connection.output.add(utf8.encode('landing angga'));
    }
    if (selectedProgram == 'Rozak - Object and Color Detection') {
      connection.output.add(utf8.encode('landing rozak'));
    }
    if (selectedProgram == 'Denta - Face Tracking') {
      connection.output.add(utf8.encode('landing denta'));
    }
    if (selectedProgram == 'Anfasa - Fire Detection') {
      connection.output.add(utf8.encode('landing anfasa'));
    }

    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
      content: Text('Land command sent'),
    ));

    _dronefly = false;

    print('Land command sent');
  }

  void _getdronelocation() async {
    connection.output.add(utf8.encode('getDroneLocation'));

    connection.input.listen((Uint8List data) {
      print('Data incoming: ${ascii.decode(data)}');
      String dataString = String.fromCharCodes(data);
      final splitted = dataString.split(',');
      setState(() {
        _origin = Marker(
          markerId: const MarkerId('origin'),
          infoWindow: const InfoWindow(title: 'Origin'),
          icon:
              BitmapDescriptor.defaultMarkerWithHue(BitmapDescriptor.hueGreen),
          position:
              new LatLng(double.parse(splitted[0]), double.parse(splitted[1])),
        );

        _destination = null;
        _destination2 = null;
        _destination3 = null;
        _destination4 = null;
      });
      ScaffoldMessenger.of(context).showSnackBar(new SnackBar(
        content: Text('$dataString'),
      ));
    });
  }

void _getfirelocation() async {
    connection.input.listen((Uint8List data) {
      print('Data incoming: ${ascii.decode(data)}');
      String dataString = String.fromCharCodes(data);
      if (dataString == '1') {
        setState(() {
          var title =
              'Destination 1 (${destCoordinate1.text})';
          _destination = Marker(
            markerId: const MarkerId('destination'),
            infoWindow: InfoWindow(title: title),
            icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueRed),
            position: new LatLng(
              double.parse(
                  destCoordinate1.text.split(',')[0]),
              double.parse(
                  destCoordinate1.text.split(',')[1]),
            ),
          );
        });
      } else if (dataString == '2') {
        setState(() {
          var title =
              'Destination 2 (${destCoordinate2.text})';
          _destination2 = Marker(
            markerId: const MarkerId('destination2'),
            infoWindow: InfoWindow(title: title),
            icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueRed),
            position: new LatLng(
              double.parse(
                  destCoordinate2.text.split(',')[0]),
              double.parse(
                  destCoordinate2.text.split(',')[1]),
            ),
          );
        });
      } else if (dataString == '3') {
        setState(() {
          var title =
              'Destination 3 (${destCoordinate3.text})';
          _destination3 = Marker(
            markerId: const MarkerId('destination3'),
            infoWindow: InfoWindow(title: title),
            icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueRed),
            position: new LatLng(
              double.parse(
                  destCoordinate3.text.split(',')[0]),
              double.parse(
                  destCoordinate3.text.split(',')[1]),
            ),
          );
        });
      } else if (dataString == '4') {
        setState(() {
          var title =
              'Destination 4 (${destCoordinate4.text})';
          _destination4 = Marker(
            markerId: const MarkerId('destination3'),
            infoWindow: InfoWindow(title: title),
            icon: BitmapDescriptor.defaultMarkerWithHue(
                BitmapDescriptor.hueRed),
            position: new LatLng(
              double.parse(
                  destCoordinate4.text.split(',')[0]),
              double.parse(
                  destCoordinate4.text.split(',')[1]),
            ),
          );
        });
      }
    });
  }

  _addDestinationCoordinate(BuildContext context) => showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('Input Destination Coordinate'),
          content: Form(
            key: _formKey,
            child: Column(
              children: [
                TextFormField(
                  controller: destCoordinate1,
                  decoration: new InputDecoration(
                    hintText: "-7.12345,110.12345",
                    labelText: "Destination 1",
                    icon: Icon(Icons.location_on_outlined),
                  ),
                  validator: (value) {
                    if (value.isEmpty) {
                      return 'Destination cannot be empty';
                    }
                    return null;
                  },
                ),
                SizedBox(
                  height: 10,
                ),
                TextFormField(
                  controller: destCoordinate2,
                  decoration: new InputDecoration(
                    hintText: "-7.12345,110.12345",
                    labelText: "Destination 2",
                    icon: Icon(Icons.location_on_outlined),
                  ),
                ),
                SizedBox(
                  height: 10,
                ),
                TextFormField(
                  controller: destCoordinate3,
                  decoration: new InputDecoration(
                    hintText: "-7.12345,110.12345",
                    labelText: "Destination 3",
                    icon: Icon(Icons.location_on_outlined),
                  ),
                ),
                SizedBox(
                  height: 10,
                ),
                TextFormField(
                  controller: destCoordinate4,
                  decoration: new InputDecoration(
                    hintText: "-7.12345,110.12345",
                    labelText: "Destination 4",
                    icon: Icon(Icons.location_on_outlined),
                  ),
                ),
                SizedBox(
                  height: 10,
                ),
                ElevatedButton(
                    child: Text(
                      "Submit",
                      style: TextStyle(color: Colors.white),
                    ),
                    onPressed: () {
                      if (_formKey.currentState.validate()) {
                        Navigator.of(context).pop();
                        if (_destination != null) {
                          setState(() {
                            _destination = null;
                          });
                        }
                        if (_destination == null) {
                          setState(() {
                            var title =
                                'Destination 1 (${destCoordinate1.text})';
                            _destination = Marker(
                              markerId: const MarkerId('destination'),
                              infoWindow: InfoWindow(title: title),
                              icon: BitmapDescriptor.defaultMarkerWithHue(
                                  BitmapDescriptor.hueBlue),
                              position: new LatLng(
                                double.parse(
                                    destCoordinate1.text.split(',')[0]),
                                double.parse(
                                    destCoordinate1.text.split(',')[1]),
                              ),
                            );
                          });
                        } else if (_destination2 == null) {
                          setState(() {
                            var title =
                                'Destination 2 (${destCoordinate2.text})';
                            _destination2 = Marker(
                              markerId: const MarkerId('destination2'),
                              infoWindow: InfoWindow(title: title),
                              icon: BitmapDescriptor.defaultMarkerWithHue(
                                  BitmapDescriptor.hueBlue),
                              position: new LatLng(
                                double.parse(
                                    destCoordinate2.text.split(',')[0]),
                                double.parse(
                                    destCoordinate2.text.split(',')[1]),
                              ),
                            );
                          });
                        } else if (_destination3 == null) {
                          setState(() {
                            var title =
                                'Destination 3 (${destCoordinate3.text})';
                            _destination3 = Marker(
                              markerId: const MarkerId('destination3'),
                              infoWindow: InfoWindow(title: title),
                              icon: BitmapDescriptor.defaultMarkerWithHue(
                                  BitmapDescriptor.hueBlue),
                              position: new LatLng(
                                double.parse(
                                    destCoordinate3.text.split(',')[0]),
                                double.parse(
                                    destCoordinate3.text.split(',')[1]),
                              ),
                            );
                          });
                        } else if (_destination4 == null) {
                          setState(() {
                            var title =
                                'Destination 4 (${destCoordinate4.text})';
                            _destination4 = Marker(
                              markerId: const MarkerId('destination3'),
                              infoWindow: InfoWindow(title: title),
                              icon: BitmapDescriptor.defaultMarkerWithHue(
                                  BitmapDescriptor.hueBlue),
                              position: new LatLng(
                                double.parse(
                                    destCoordinate4.text.split(',')[0]),
                                double.parse(
                                    destCoordinate4.text.split(',')[1]),
                              ),
                            );
                          });
                        }
                      }
                    }),
              ],
            ),
          ),
        );
      });
}