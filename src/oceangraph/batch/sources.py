"""Local marine source selection helpers; importing has no side effects."""
import re

TOPICS = {
 'carbon_pump_flux': r'biological (?:carbon )?pump|carbon export|carbon sequestration|air.sea|carbon flux|carbon sink|pco2|fco2',
 'acidification_carbonate': r'ocean acidification|carbonate|aragonite|calcification|calcifying|acidification',
 'nutrients_microbes': r'nitrogen|nitrification|denitrification|nutrient|phosphorus|microbial|microorganism',
 'coastal_blue_carbon': r'mangrove|seagrass|salt marsh|coastal wetland|blue carbon|estuar',
 'physical_climate': r'circulation|upwelling|stratification|ocean warming|marine heatwave|thermohaline|ocean heat|el ni.o|mixing',
 'ecology_plankton': r'phytoplankton|zooplankton|plankton|coral|bloom|biodiversity|food web|copepod',
 'observing_models': r'remote sensing|satellite|argo|autonomous|biogeochemical model|ocean model|sensor|ocean colour|ocean color',
 'sediment_paleo': r'paleo|palaeo|sediment|isotope|glacial|eocene|holocene|cretaceous|pleistocene',
}
MARINE = re.compile(r'ocean|marine|seawater|sea\b|seas\b|seagrass|coral|mangrove|coastal|estuar|phytoplankton|zooplankton|arctic|antarctic|upwelling|pelagic|continental shelf|blue carbon', re.I)


def field(header, name):
    m = re.search(rf'(?m)^{name}:\s*(.+)$', header)
    return m.group(1).strip().strip('"\'') if m else ''


def source_context(body):
    body = re.split(r'(?im)^#{1,3}\s*(?:references|acknowledg\w*|author contributions|funding|data availability)\b', body)[0]
    sections = re.split(r'(?m)^(?=##\s+)', body)
    selected = []
    for pattern, allowance in [(r'abstract', 3000), (r'results', 5000), (r'conclusion|discussion', 2500)]:
        found = next((s for s in sections if re.search(pattern, s.split('\n', 1)[0], re.I)), None)
        if found:
            selected.append(found[:allowance])
    if len(''.join(selected)) < 4000:
        selected.append(body[:9000])
    text = '\n\n'.join(dict.fromkeys(selected))[:10500]
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 55]
    chunks, buffer = [], ''
    for paragraph in paragraphs:
        # A paragraph cut at the source limit ends at its last complete sentence.
        if len(paragraph) > 3800:
            pieces = re.split(r'(?<=[.!?])\s+(?=[A-Z])', paragraph)
        else:
            pieces = [paragraph]
        for piece in pieces:
            if buffer and len(buffer) + len(piece) > 2700:
                chunks.append(buffer.strip())
                buffer = ''
            buffer += piece + '\n\n'
    if buffer.strip():
        chunks.append(buffer.strip())
    return chunks[:5]
