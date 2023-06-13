#!/usr/bin/python

"""
This profile is intended for doing any experiment using Shout. 

This profile can allocate X310 radios (+ compute), FE NUC1+B210, FE NUC2+B210, ME, and compute node (for Shout's orchestrator). 

Instructions:
**1) Instantiate this profile with appropriate parameters**

At the "Parameterize" step, add radios that are needed for your planned experiment. Also, speceify the freqeuncy ranges if you are planning to use transmitter(s) in your experiment. 


You can leave the other parameters in this profile at their defaults.

Once you have these parameters selected, click through the rest of the
profile and then click "Finish" to instantiate.  It will take 10
to 15 minutes for the experiment to finish setting up.  Once it
is "green", proceed to the next step.


**2) Open SSH sessions**

Use the following commands to start ssh and tmux sessions for the orchestor:
```
ssh -Y -p 22 -t <username>@<orch_node_hostname> 'cd /local/repository/bin && tmux new-session -A -s shout1 &&  exec $SHELL'
ssh -Y -p 22 -t <username>@<orch_node_hostname> 'cd /local/repository/bin && tmux new-session -A -s shout2 &&  exec $SHELL'
```

Use the following command to start a ssh and tmux session for each of the radio:
```
ssh -Y -p 22 -t <username>@<radio_hostname> 'cd /local/repository/bin && tmux new-session -A -s shout &&  exec $SHELL'
```

Reference SSH commands can be seen on the "List View" tab next to the
compute node names.  

TMUX is helpful for doing multiple terminal sessions and allowing remote sessions to remain active even when the SSH connection to the nodes gets disconncted.


**3) Check radio firmware on x310 (rooftop site) radios**

On each of the `cellsdr1-<site>-comp` and `cbrssdr1-<site>-comp` nodes, run `uhd_usrp_probe`.  If
the output complains about a firmware mismatch, run: 

```
./setup_x310.sh
```

After the firmware update finishes, find the corresponding X310 radio devices in the "List View" on the
POWDER web UI.  Click the checkbox for each device row where a
firmware update was executed, then click the "gear" icon at the top of
the column and select "power cycle selected".  Confirm to complete the
operation and wait about 10 seconds for the devices to come back
online.  Double check that the firmware has updated by running
`uhd_usrp_probe` again.


**4) Start the Shout Orchestrator process**

In one of your `orch` SSH sessions, run:

```
./1.start_orch.sh
```

This will start the Shout orchestrator that all of the measurement
clients, and command executor script will connect to.


**5) Start measurement clients**

In the SSH session for each of the nodes, run: 

```
./2.start_client.sh
```

You should see these clients connect both in the output of the client, and
in the output of the orchestrator.


**6) Execute a measurement run**

With all clients connected to the orchestrator, you can now perform a
measurement collection run.  There are example JSON cmd files located
in: https://gitlab.flux.utah.edu/aniqua/shout/-/tree/master/examples/cmdfiles and /local/repository/etc/cmdfiles.  Select one and adjust according to your experiment plan. Once the command
file is properly adjusted, update 3.run_cmd.sh to point to the correct cmd file and output location. 
Next, in your other `orch` SSH session, run:

```
./3.run_cmd.sh
```
This will run the Shout command(s) as specified in the cmd file. This will create a measurement directory in OUT named Shout\_meas\_<date>_<time> with the following items:

a) measurements.hdf5: Measurement dataset.

b) <cmd>.json: Cmd file used for the measurement.

c) log: Log file saved by Shout's measiface.py.

d) configuration.csv: Current POWDER radio configuration file from https://gitlab.flux.utah.edu/powderrenewpublic/powder-deployment.

e) powder-deployment.csv: Current POWDER deployment file from https://gitlab.flux.utah.edu/powderrenewpublic/powder-deployment.

f) bus<bus number>_locations.csv files: GPSd location and speed information files, one for each of the buses used in the measurement. 

Details of supported commands are available in https://gitlab.flux.utah.edu/aniqua/shout/-/blob/master/README.md.

Example measurement directories are in https://gitlab.flux.utah.edu/aniqua/shout/-/tree/master/examples.


**6) Check saved dataset**

You can run the following command to test saved measurements.hdf5:

```
cd /local/repository/shout
python3 check-data.py --datadir <shout_meas_dir>
```

"""

# Library imports
import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab.pnext as pn
import geni.rspec.emulab.spectrum as spectrum
import geni.rspec.igext as ig
import geni.rspec.emulab.route as route


# Global Variables
meas_disk_image = \
        "urn:publicid:IDN+emulab.net+image+PowderTeam:U18-GR-PBUF"
orch_image = meas_disk_image
x310_node_image = meas_disk_image
nuc_image = meas_disk_image
sm_image = meas_disk_image

# List of CBAND rooftop X310 radios.
cband_radios = [
    ("cbrssdr1-bes",
     "Behavioral"),
    ("cbrssdr1-browning",
     "Browning"),
    ("cbrssdr1-dentistry",
     "Dentistry"),
    ("cbrssdr1-fm",
     "Friendship Manor"),
    ("cbrssdr1-hospital",
     "Hospital"),
    ("cbrssdr1-honors",
     "Honors"),
    ("cbrssdr1-meb",
     "MEB"),
    ("cbrssdr1-smt",
     "SMT"),
    ("cbrssdr1-ustar",
     "USTAR"),
]

# List of Cellular radios
cell_radios = [
    ("cellsdr1-bes",
     "Behavioral"),
    ("cellsdr1-browning",
     "Browning"),
    ("cellsdr1-dentistry",
     "Dentistry"),
    ("cellsdr1-fm",
     "Friendship Manor"),
    ("cellsdr1-hospital",
     "Hospital"),
    ("cellsdr1-honors",
     "Honors"),
    ("cellsdr1-meb",
     "MEB"),
    ("cellsdr1-smt",
     "SMT"),
    ("cellsdr1-ustar",
     "USTAR"),
]

# A list of endpoint sites.
fe_sites = [
    ('urn:publicid:IDN+bookstore.powderwireless.net+authority+cm',
     "Bookstore"),
    ('urn:publicid:IDN+cpg.powderwireless.net+authority+cm',
     "Garage"),
    ('urn:publicid:IDN+ebc.powderwireless.net+authority+cm',
     "EBC"),
    ('urn:publicid:IDN+guesthouse.powderwireless.net+authority+cm',
     "GuestHouse"),
    ('urn:publicid:IDN+humanities.powderwireless.net+authority+cm',
     "Humanities"),
    ('urn:publicid:IDN+law73.powderwireless.net+authority+cm',
     "Law73"),
    ('urn:publicid:IDN+madsen.powderwireless.net+authority+cm',
     "Madsen"),
    ('urn:publicid:IDN+moran.powderwireless.net+authority+cm',
     "Moran"),
    ('urn:publicid:IDN+sagepoint.powderwireless.net+authority+cm',
     "SagePoint"),
    ('urn:publicid:IDN+web.powderwireless.net+authority+cm',
     "WEB"),
]

# A list of mobile endpoint sites.
me_sites = [
    ("All", "All"),
]

# List of OTA lab X310 radios.
ota_x310_radios = [
    "ota-x310-1",
    "ota-x310-2",
    "ota-x310-3",
    "ota-x310-4",
]

# List of OTA lab NUC+B210 devices.
ota_b210_devices = [
    "ota-nuc1",
    "ota-nuc2",
    "ota-nuc3",
    "ota-nuc4",
]

# List of PhantomNet devices and links.
pn_devices = [
    "nuc1-nuc2",
    "nuc2-nuc3",
    "nuc3-nuc4",
    "nuc1-nuc4",
    "nuc5-nuc6",
    "nuc1-nuc2-nuc3",
    "nuc1-nuc4-nuc3",
    "nuc1-nuc2-nuc3-nuc4-nuc1"
]

# List of dense radios.
dense_radios = [
    ("cnode-wasatch",
     "Wasatch"),
    ("cnode-mario",
     "Mario"),
    ("cnode-moran",
     "Moran"),
    ("cnode-guesthouse",
     "Guesthouse"),
    ("cnode-ebc",
     "EBC"),
    ("cnode-ustar",
     "USTAR"),
]

freq_ranges = {
    "ISM-900": [914.87, 915.13],
    "ISM-2400": [2400.00, 2483.50],
    "CBAND": [3550.00, 3700.00], 
    "ISM-5800": [5725.00, 5850.00]
}

datasets = {
    "SpectSet": "urn:publicid:IDN+emulab.net:nrdz+ltdataset+SpectSet",
    "ADSBRecordings": "urn:publicid:IDN+emulab.net:powdersandbox+stdataset+ADSBrecordings"
}

# Top-level request object.
request = portal.context.makeRequestRSpec()

# Helper function that allocates a PC + X310 radio pair, with Ethernet
# link between them.
def x310_node_pair(x310_radio_name, node_type, start_vnc = False, ignore_isbw = False):
    radio_link = request.Link("%s-link" % x310_radio_name)
    radio_link.bandwidth = 10*1000*1000 # 10Gbps expressed in Kbps
    if ignore_isbw:
        radio_link.best_effort = True

    node = request.RawPC("%s-comp" % x310_radio_name)
    node.hardware_type = node_type
    node.disk_image = x310_node_image
    if start_vnc:
        node.startVNC()

    #node.addService(rspec.Execute(shell="bash",command=x310_setup_cmd))

    node_radio_if = node.addInterface("usrp_if")
    node_radio_if.addAddress(rspec.IPv4Address("192.168.40.1",
                                               "255.255.255.0"))
    radio_link.addInterface(node_radio_if)

    radio = request.RawPC("%s-x310" % x310_radio_name)
    radio.component_id = x310_radio_name
    radio_link.addNode(radio)


# Helper function to connect orch to a dataset
def connect_to_dataset(node, dataset_name):
    # We need a link to talk to the remote file system, so make an interface.
    iface = node.addInterface()

    # The remote file system is represented by special node.
    fsnode = request.RemoteBlockstore("fsnode", "/" + dataset_name)

    # This URN is displayed in the web interfaace for your dataset.
    fsnode.dataset = datasets[dataset_name]
    #
    # The "rwclone" attribute allows you to map a writable copy of the
    # indicated SAN-based dataset. In this way, multiple nodes can map
    # the same dataset simultaneously. In many situations, this is more
    # useful than a "readonly" mapping. For example, a dataset
    # containing a Linux source tree could be mapped into multiple
    # nodes, each of which could do its own independent,
    # non-conflicting configure and build in their respective copies.
    # Currently, rwclones are "ephemeral" in that any changes made are
    # lost when the experiment mapping the clone is terminated.
    #
    fsnode.rwclone = False

    #
    # The "readonly" attribute, like the rwclone attribute, allows you to
    # map a dataset onto multiple nodes simultaneously. But with readonly,
    # those mappings will only allow read access (duh!) and any filesystem
    # (/mydata in this example) will thus be mounted read-only. Currently,
    # readonly mappings are implemented as clones that are exported
    # allowing just read access, so there are minimal efficiency reasons to
    # use a readonly mapping rather than a clone. The main reason to use a
    # readonly mapping is to avoid a situation in which you forget that
    # changes to a clone dataset are ephemeral, and then lose some
    # important changes when you terminate the experiment.
    #
    fsnode.readonly = False
    
    # Now we add the link between the node and the special node
    fslink = request.Link("fslink")
    fslink.addInterface(iface)
    fslink.addInterface(fsnode.interface)

    # Special attributes for this link that we must use.
    fslink.best_effort = True
    fslink.vlan_tagging = True


# Node type parameter for PCs to be paired with X310 radios.
# Restricted to those that are known to work well with them.
portal.context.defineParameter(
    "nodetype",
    "Compute node type",
    portal.ParameterType.STRING, "d740",
    ["d740","d430"],
    "Type of compute node to be paired with the X310 Radios",
)

# Node type for the orchestrator.
portal.context.defineParameter(
    "orchtype",
    "Orchestrator node type",
    portal.ParameterType.STRING, "d740",
    ["None", "d430","d740", "d710", ""],
    "Type of compute node for the orchestrator (unset == 'any available')",
)

portal.context.defineParameter(
    "dataset",
    "Dataset to connect",
    portal.ParameterType.STRING, "SpectSet",
    ["SpectSet","ADSBRecordings","None"],
    "Name of the remote dataset to connect with orch",
)

# Set of Mobile Endpoint devices to allocate
portal.context.defineStructParameter(
    "me_radio_sites", "Mobile Endpoint Sites", [],
    multiValue=True,
    min=0,
    multiValueTitle="Mobile Endpoint Supermicro+B210 radios.",
    members=[
        portal.Parameter(
            "site",
            "ME Site",
            portal.ParameterType.STRING,
            me_sites[0], me_sites,
            longDescription="An `ed1` device will be selected at the site."
        ),
    ])

# Set of Cellular X310 radios to allocate
portal.context.defineStructParameter(
    "cell_radio_sites", "Cellular Radio Sites", [],
    multiValue=True,
    min=0,
    multiValueTitle="Cellular X310 radios to allocate.",
    members=[
        portal.Parameter(
            "radio",
            "Cellular Radio Site",
            portal.ParameterType.STRING,
            cell_radios[0], cell_radios,
            longDescription="Cellular X310 radio will be allocated from selected site."
        ),
    ])

# Set of Fixed Endpoint devices to allocate (nuc2)
portal.context.defineStructParameter(
    "fe_radio_sites_nuc2", "Fixed Endpoint Sites", [],
    multiValue=True,
    min=0,
    multiValueTitle="Cellular Fixed Endpoint NUC2+B210 radios.",
    members=[
        portal.Parameter(
            "site",
            "FE Site",
            portal.ParameterType.STRING,
            fe_sites[0], fe_sites,
            longDescription="A `nuc2` device will be selected at the site."
        ),
    ])

# Set of CBAND X310 radios to allocate
portal.context.defineStructParameter(
    "cband_radio_sites", "CBAND Radio Sites", [],
    multiValue=True,
    min=0,
    multiValueTitle="CBAND X310 radios.",
    members=[
        portal.Parameter(
            "radio",
            "CBAND Radio Site",
            portal.ParameterType.STRING,
            cband_radios[0], cband_radios,
            longDescription="CBAND X310 radio will be allocated from selected site."
        ),
    ])

# Set of Fixed Endpoint devices to allocate (nuc1)
portal.context.defineStructParameter(
    "fe_radio_sites_nuc1", "Fixed Endpoint Sites", [],
    multiValue=True,
    min=0,
    multiValueTitle="Fixed Endpoint NUC1+B210 radios.",
    members=[
        portal.Parameter(
            "site",
            "FE Site",
            portal.ParameterType.STRING,
            fe_sites[0], fe_sites,
            longDescription="A `nuc1` device will be selected at the site."
        ),
    ])

# Set of OTA Lab X310 radios to allocate
portal.context.defineStructParameter(
    "ota_lab_x310s", "OTA Lab X310 Radios", [],
    multiValue=True,
    min=0,
    multiValueTitle="OTA Lab X310 radios.",
    members=[
        portal.Parameter(
            "radio",
            "OTA Lab Radio",
            portal.ParameterType.STRING,
            ota_x310_radios[0], ota_x310_radios,
            longDescription="An X310 radio in the OTA Lab along with associated compute node will be allocated."
        ),
    ])

# Set of OTA Lab NUC+B210 devices to allocate
portal.context.defineStructParameter(
    "ota_lab_b210s", "OTA Lab B210 Radios", [],
    multiValue=True,
    min=0,
    multiValueTitle="OTA Lab NUC+B210 radios.",
    members=[
        portal.Parameter(
            "device",
            "NUC+B210 device",
            portal.ParameterType.STRING,
            ota_b210_devices[0], ota_b210_devices,
            longDescription="A NUC+B210 device in the OTA lab will be allocated."
        ),
    ])

# Set of Dense Deployment radio sites to allocate
portal.context.defineStructParameter(
    "dense_radios", "Dense Site Radios", [],
    multiValue=True,
    min=0,
    multiValueTitle="Dense Site NUC+B210 radios to allocate.",
    members=[
        portal.Parameter(
            "device",
            "SFF Compute + NI B210 device",
            portal.ParameterType.STRING,
            dense_radios[0], dense_radios,
            longDescription="A Small Form Factor compute with attached NI B210 device at the given Dense Deployment site will be allocated."
        ),
    ])


# Set of PhantonNet radios to allocate
portal.context.defineStructParameter(
    "phantomnet", "PhantonNet Radios", [],
    multiValue=True,
    min=0,
    max=1,
    multiValueTitle="PhantomNet radios and links to allocate.",
    members=[
        portal.Parameter(
            "device",
            "PhantomNet radios and links",
            portal.ParameterType.STRING,
            pn_devices[0], pn_devices,
            longDescription="PhantomNet radios will be allocated and corresponding links will be created."
        ),
    ])

### Frequency/spectrum parameters

# CBAND
portal.context.defineStructParameter(
    "cband_freq_ranges", "CBAND Frequency Ranges", [],
    multiValue=True,
    min=0,
    multiValueTitle="Frequency ranges for CBAND operation.",
    members=[
        portal.Parameter(
            "freq_min",
            "Frequency Min",
            portal.ParameterType.BANDWIDTH,
            freq_ranges["CBAND"][0],
            longDescription="Values are rounded to the nearest kilohertz."
        ),
        portal.Parameter(
            "freq_max",
            "Frequency Max",
            portal.ParameterType.BANDWIDTH,
            freq_ranges["CBAND"][0] + 10.0,
            longDescription="Values are rounded to the nearest kilohertz."
        ),
    ])

# ISM - 900MHz
portal.context.defineStructParameter(
    "ism900_freq_ranges", "ISM-900 Frequency Ranges", [],
    multiValue=True,
    min=0,
    multiValueTitle="Frequency ranges for ISM-900 operation.",
    members=[
        portal.Parameter(
            "freq_min",
            "Frequency Min",
            portal.ParameterType.BANDWIDTH,
            freq_ranges["ISM-900"][0],
            longDescription="Values are rounded to the nearest kilohertz."
        ),
        portal.Parameter(
            "freq_max",
            "Frequency Max",
            portal.ParameterType.BANDWIDTH,
            freq_ranges["ISM-900"][0] + 10.0,
            longDescription="Values are rounded to the nearest kilohertz."
        ),
    ])

# ISM - 2400MHz
portal.context.defineStructParameter(
    "ism2400_freq_ranges", "ISM-2400 Frequency Ranges", [],
    multiValue=True,
    min=0,
    multiValueTitle="Frequency ranges for ISM-2400 operation.",
    members=[
        portal.Parameter(
            "freq_min",
            "Frequency Min",
            portal.ParameterType.BANDWIDTH,
            freq_ranges["ISM-2400"][0],
            longDescription="Values are rounded to the nearest kilohertz."
        ),
        portal.Parameter(
            "freq_max",
            "Frequency Max",
            portal.ParameterType.BANDWIDTH,
            freq_ranges["ISM-2400"][0] + 10.0,
            longDescription="Values are rounded to the nearest kilohertz."
        ),
    ])

# Start VNC?
portal.context.defineParameter("start_vnc",
                               "Start X11 VNC on all compute nodes",
                               portal.ParameterType.BOOLEAN, True)

# Start VNC?
portal.context.defineParameter("ignore_isbw",
                               "Ignore interswitch bandwith limitations on radio-to-compute links. (Do not use unless you have a specific reason to do so.)",
                               portal.ParameterType.BOOLEAN, False,
                               advanced=True)

# Bind and verify parameters
params = portal.context.bindParameters()

for i, frange in enumerate(params.cband_freq_ranges):
    if frange.freq_min < 3400 or frange.freq_min > 3800 \
       or frange.freq_max < 3400 or frange.freq_max > 3800:
        perr = portal.ParameterError("CBAND frequencies must be between 3358 and 3700 MHz", ["cband_freq_ranges[%d].freq_min" % i, "cband_freq_ranges[%d].freq_max" % i])
        portal.context.reportError(perr)
    if frange.freq_max - frange.freq_min < 1:
        perr = portal.ParameterError("Minimum and maximum frequencies must be separated by at least 1 MHz", ["cband_freq_ranges[%d].freq_min" % i, "cband_freq_ranges[%d].freq_max" % i])
        portal.context.reportError(perr)

for i, frange in enumerate(params.ism900_freq_ranges):
    if frange.freq_min < freq_ranges["ISM-900"][0] or frange.freq_min > freq_ranges["ISM-900"][1] \
       or frange.freq_max < freq_ranges["ISM-900"][0] or frange.freq_max > freq_ranges["ISM-900"][1]:
        perr = portal.ParameterError("ISM-900 frequencies must be between %f and %f MHz" % (freq_ranges["ISM-900"][0], freq_ranges["ISM-900"][1]), ["ism900_freq_ranges[%d].freq_min" % i, "ism900_freq_ranges[%d].freq_max" % i])
        portal.context.reportError(perr)
    if frange.freq_max - frange.freq_min < .2:
        perr = portal.ParameterError("Minimum and maximum frequencies must be separated by at least 200 KHz", ["ism900_freq_ranges[%d].freq_min" % i, "ism900_freq_ranges[%d].freq_max" % i])
        portal.context.reportError(perr)

for i, frange in enumerate(params.ism2400_freq_ranges):
    if frange.freq_min < freq_ranges["ISM-2400"][0] or frange.freq_min > freq_ranges["ISM-2400"][1] \
       or frange.freq_max < freq_ranges["ISM-2400"][0] or frange.freq_max > freq_ranges["ISM-2400"][1]:
        perr = portal.ParameterError("ISM-2400 frequencies must be between %f and %f MHz" % (freq_ranges["ISM-2400"][0], freq_ranges["ISM-2400"][1]), ["ism2400_freq_ranges[%d].freq_min" % i, "ism2400_freq_ranges[%d].freq_max" % i])
        portal.context.reportError(perr)
    if frange.freq_max - frange.freq_min < 1:
        perr = portal.ParameterError("Minimum and maximum frequencies must be separated by at least 1 MHz", ["ism2400_freq_ranges[%d].freq_min" % i, "ism2400_freq_ranges[%d].freq_max" % i])
        portal.context.reportError(perr)

# Now verify.
portal.context.verifyParameters()

# Declare that we may be starting X11 VNC on the compute nodes.
if params.start_vnc:
    request.initVNC()

# Allocate orchestrator node
if params.orchtype != "None":
    orch = request.RawPC("orch")
    orch.disk_image = orch_image
    orch.hardware_type = params.orchtype
    if params.start_vnc:
        orch.startVNC()
    if params.dataset != "None": 
        connect_to_dataset(orch, params.dataset)

# Request PhantomNet radios
for dev in params.phantomnet:
    node_names = dev.device.split('-')
    n_nodes = len(node_names)
    if node_names[0] == node_names[-1]: # for nuc1-nuc2-nuc3-nuc4-nuc1
        node_names = node_names[:-1]
    
    nodes = []
    for node_name in node_names:
        node = request.RawPC(node_name)
        node.hardware_type = "nuc5300"
        node.component_id = node_name
        node.disk_image = meas_disk_image
        if params.start_vnc:
            node.startVNC()
        nodes.append(node)

    if n_nodes == 2:
        node0if0 = nodes[0].addInterface("n0rf0")
        node1if0 = nodes[1].addInterface("n1rf0")  

        rflink0 = request.RFLink("rflink0")
        rflink0.addInterface(node0if0)
        rflink0.addInterface(node1if0)

    elif n_nodes == 3:
        node0if = nodes[0].addInterface("n0rf0")

        node1if0 = nodes[1].addInterface("n1rf0")  
        node1if1 = nodes[1].addInterface("n1rf1")

        node2if = nodes[2].addInterface("n2rf0")

        rflink0 = request.RFLink("rflink0")
        rflink0.addInterface( node0if )
        rflink0.addInterface( node1if0 )

        rflink1 = request.RFLink("rflink1")
        rflink1.addInterface(node1if1)
        rflink1.addInterface(node2if)

    elif n_nodes == 5:
        node0if0 = nodes[0].addInterface("n0rf0")
        node0if1 = nodes[0].addInterface("n0rf1")

        node1if0 = nodes[1].addInterface("n1rf0")  
        node1if1 = nodes[1].addInterface("n1rf1")

        node2if0 = nodes[2].addInterface("n2rf0")
        node2if1 = nodes[2].addInterface("n2rf1")

        node3if0 = nodes[3].addInterface("n3rf0")
        node3if1 = nodes[3].addInterface("n3rf1")

        rflink0 = request.RFLink("rflink0")
        rflink0.addInterface(node0if0)
        rflink0.addInterface(node1if0)

        rflink1 = request.RFLink("rflink1")
        rflink1.addInterface(node1if1)
        rflink1.addInterface(node2if0)

        rflink2 = request.RFLink("rflink2")
        rflink2.addInterface(node2if1)
        rflink2.addInterface(node3if0)

        rflink3 = request.RFLink("rflink3")
        rflink3.addInterface(node3if1)
        rflink3.addInterface(node0if1)

# Request PC + CBAND X310 resource pairs.
for rsite in params.cband_radio_sites:
    x310_node_pair(rsite.radio, params.nodetype, params.start_vnc, params.ignore_isbw)

# Request PC + Cellular X310 resource pairs.
for rsite in params.cell_radio_sites:
    x310_node_pair(rsite.radio, params.nodetype, params.start_vnc, params.ignore_isbw)

# Request PC + OTA Lab X310 resource pairs.
for dev in params.ota_lab_x310s:
    x310_node_pair(dev.radio, params.nodetype, params.start_vnc, params.ignore_isbw)

# Request nuc1+B210 radio resources at FE sites.
for fesite in params.fe_radio_sites_nuc1:
    nuc = ""
    for urn,sname in fe_sites:
        if urn == fesite.site:
            nuc = request.RawPC("%s-nuc1-b210" % sname)
            break
    nuc.component_manager_id = fesite.site
    nuc.component_id = "nuc1"
    nuc.disk_image = nuc_image
    if params.start_vnc:
        nuc.startVNC()

# Request nuc2+B210 radio resources at FE sites.
for fesite in params.fe_radio_sites_nuc2:
    nuc = ""
    for urn,sname in fe_sites:
        if urn == fesite.site:
            nuc = request.RawPC("%s-nuc2-b210" % sname)
            break
    nuc.component_manager_id = fesite.site
    nuc.component_id = "nuc2"
    nuc.disk_image = nuc_image
    if params.start_vnc:
        nuc.startVNC()

# Request ed1+B210 radio resources at ME sites.
for mesite in params.me_radio_sites:
    if mesite.site == "All":
        obj = request.requestAllRoutes()
        obj.disk_image = nuc_image
        if params.start_vnc:
            obj.startVNC()
    else:
        node = ""
        for urn,sname in me_sites:
            if urn == mesite.site:
                node = request.RawPC("%s-b210" % sname)
                node.component_manager_id = mesite.site
                node.component_id = "ed1"
                node.disk_image = nuc_image
                break

# Request NUC+B210 radio resources at the requested Dense Deployment sites.
for dev in params.dense_radios:
    node = request.RawPC("%s-dd-b210" % dev.device)
    node.component_id = dev.device
    node.disk_image = sm_image
    if params.start_vnc:
        node.startVNC()
 
# Request NUC+B210 radio resources in the OTA Lab.
for dev in params.ota_lab_b210s:
    node = request.RawPC("%s-b210" % dev.device)
    node.component_id = dev.device
    node.disk_image = sm_image
    if params.start_vnc:
        node.startVNC()

# Request frequency range(s)
for frange in params.cband_freq_ranges:
    request.requestSpectrum(frange.freq_min, frange.freq_max, 0)

for frange in params.ism900_freq_ranges:
    request.requestSpectrum(frange.freq_min, frange.freq_max, 0)

for frange in params.ism2400_freq_ranges:
    request.requestSpectrum(frange.freq_min, frange.freq_max, 0)
    
# Emit!
portal.context.printRequestRSpec()
