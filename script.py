import xml.etree.ElementTree as ET
import re

# Basic JMeter XML structure (skeleton)
JMX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<jmeterTestPlan version="1.2" properties="5.0" jmeter="5.5">
  <hashTree>
    <TestPlan guiclass="TestPlanGui" testclass="TestPlan" testname="Converted from ReadyAPI" enabled="true">
      <stringProp name="TestPlan.comments"></stringProp>
      <boolProp name="TestPlan.functional_mode">false</boolProp>
      <boolProp name="TestPlan.serialize_threadgroups">false</boolProp>
      <elementProp name="TestPlan.user_defined_variables" elementType="Arguments" guiclass="ArgumentsPanel" testclass="Arguments" enabled="true">
        <collectionProp name="Arguments.arguments"/>
      </elementProp>
      <stringProp name="TestPlan.user_define_classpath"></stringProp>
    </TestPlan>
    <hashTree>
      <ThreadGroup guiclass="ThreadGroupGui" testclass="ThreadGroup" testname="Thread Group" enabled="true">
        <stringProp name="ThreadGroup.num_threads">1</stringProp>
        <stringProp name="ThreadGroup.ramp_time">1</stringProp>
        <longProp name="ThreadGroup.start_time">0</longProp>
        <longProp name="ThreadGroup.end_time">0</longProp>
        <boolProp name="ThreadGroup.scheduler">false</boolProp>
        <stringProp name="ThreadGroup.on_sample_error">continue</stringProp>
      </ThreadGroup>
      <hashTree>
        {samplers}
      </hashTree>
    </hashTree>
  </hashTree>
</jmeterTestPlan>
"""

# Template for a single HTTP Sampler with optional Header Manager + Assertion
HTTP_SAMPLER = """
<HTTPSamplerProxy guiclass="HttpTestSampleGui" testclass="HTTPSamplerProxy" testname="{name}" enabled="true">
  <stringProp name="HTTPSampler.domain">{domain}</stringProp>
  <stringProp name="HTTPSampler.port"></stringProp>
  <stringProp name="HTTPSampler.protocol">{protocol}</stringProp>
  <stringProp name="HTTPSampler.path">{path}</stringProp>
  <stringProp name="HTTPSampler.method">{method}</stringProp>
  <boolProp name="HTTPSampler.postBodyRaw">true</boolProp>
  <elementProp name="HTTPsampler.Arguments" elementType="Arguments">
    <collectionProp name="Arguments.arguments"/>
  </elementProp>
  <stringProp name="HTTPSampler.body">{body}</stringProp>
</HTTPSamplerProxy>
<hashTree>
{headers}
{assertions}
</hashTree>
"""

HEADER_MANAGER = """
<HeaderManager guiclass="HeaderPanel" testclass="HeaderManager" testname="HTTP Header Manager" enabled="true">
  <collectionProp name="HeaderManager.headers">
    {header_elements}
  </collectionProp>
</HeaderManager>
<hashTree/>
"""

HEADER_ELEMENT = """
<elementProp name="" elementType="Header">
  <stringProp name="Header.name">{name}</stringProp>
  <stringProp name="Header.value">{value}</stringProp>
</elementProp>
"""

ASSERTION = """
<ResponseAssertion guiclass="AssertionGui" testclass="ResponseAssertion" testname="Response Assertion" enabled="true">
  <collectionProp name="Asserion.test_strings">
    <stringProp name="">{contains}</stringProp>
  </collectionProp>
  <stringProp name="Assertion.test_field">Assertion.response_data</stringProp>
  <boolProp name="Assertion.assume_success">false</boolProp>
  <intProp name="Assertion.test_type">2</intProp>
</ResponseAssertion>
<hashTree/>
"""


def convert_placeholders(text: str) -> str:
    """Convert ReadyAPI property expansions like ${#Project#username} to JMeter ${username}."""
    if not text:
        return ""
    # Match ${#Scope#var} or ${#var}
    return re.sub(r"\$\{#?[A-Za-z]*#?([A-Za-z0-9_]+)\}", r"${\1}", text)


def readyapi_to_jmeter(input_file, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    ns = {"con": "http://eviware.com/soapui/config"}  # ReadyAPI namespace

    samplers_xml = []

    for req in root.findall(".//con:request", ns):
        name = req.get("name", "Request")
        method = req.get("method", "GET")
        endpoint = convert_placeholders(req.findtext("con:endpoint", default="", namespaces=ns))
        body = convert_placeholders(req.findtext("con:requestContent", default="", namespaces=ns))

        protocol = "https" if endpoint.startswith("https") else "http"
        domain = endpoint.replace("https://", "").replace("http://", "").split("/")[0]
        path = "/".join(endpoint.replace("https://", "").replace("http://", "").split("/")[1:])

        # Extract headers (if any)
        header_elements = []
        for header in req.findall(".//con:header", ns):
            h_name = convert_placeholders(header.get("name", ""))
            h_value = convert_placeholders(header.text or "")
            header_elements.append(HEADER_ELEMENT.format(name=h_name, value=h_value))
        headers_xml = HEADER_MANAGER.format(header_elements="\n".join(header_elements)) if header_elements else ""

        # Extract assertions (simple contains check)
        assertions_xml = []
        for assertion in req.findall(".//con:assertion", ns):
            contains = convert_placeholders(assertion.text or "")
            if contains.strip():
                assertions_xml.append(ASSERTION.format(contains=contains))
        assertions_block = "\n".join(assertions_xml)

        sampler = HTTP_SAMPLER.format(
            name=name,
            domain=domain,
            protocol=protocol,
            path="/" + path if path else "",
            method=method,
            body=body,
            headers=headers_xml,
            assertions=assertions_block
        )
        samplers_xml.append(sampler)

    jmx_content = JMX_TEMPLATE.format(samplers="\n".join(samplers_xml))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(jmx_content)

    print(f"Converted ReadyAPI XML → JMeter JMX saved at {output_file}")


# Example usage:
# readyapi_to_jmeter("ReadyAPI-project.xml", "Converted-TestPlan.jmx")
