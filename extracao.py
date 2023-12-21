import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime

url = 'https://rondonia.ro.gov.br/supel/licitacoes/'

def extract_id_from_url(url):
    match = re.search(r'/(\d+)/?$', url)
    if match:
        return match.group(1)
    else:
        match = re.search(r'p=(\d+)$', url)
        return match.group(1) if match else 'Não encontrado'

def extract_additional_info(item_url):
    response = requests.get(item_url)
    if response.status_code == 200:
        item_soup = BeautifulSoup(response.text, 'html.parser')

        table_elem = item_soup.find('table', class_='table-condensed')
        rows = table_elem.find_all('tr')

        valor_estimado = 'Não encontrado'
        situacao = 'Não encontrado'
        data_abertura = 'Não encontrado'
        modalidade = 'Não encontrado'

        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                header = cells[0].text.strip()
                value = cells[1].text.strip()

                if 'Valor Estimado' in header:
                    valor_estimado = extract_monetary_value(value)
                elif 'Situação' in header:
                    situacao = value
                elif 'Data da Abertura' in header:
                    data_abertura = value
                elif 'Modalidade' in header:
                    modalidade = value

        unidade_administrativa_elem = item_soup.find('td', string=re.compile(r'Unidade Administrativa', re.IGNORECASE))
        unidade_administrativa = unidade_administrativa_elem.find_next('td').text.strip() if unidade_administrativa_elem else 'Não encontrado'

        edital_icon_elem = item_soup.find('i', class_='icon-download')
        edital_link_elem = edital_icon_elem.find_parent('a') if edital_icon_elem else None
        edital_link = edital_link_elem['href'] if edital_link_elem and 'href' in edital_link_elem.attrs else 'Não encontrado'

        objeto_elem = item_soup.find('h4', class_='bolder', string='Objeto')
        descricao_completa_elem = objeto_elem.find_next('div') if objeto_elem else None
        descricao_completa = descricao_completa_elem.get_text(strip=True) if descricao_completa_elem else 'Não encontrado'

        id_from_url = extract_id_from_url(item_url)

        return {
            'Id': id_from_url,
            'Unidade Administrativa': unidade_administrativa,
            'Valor Estimado': valor_estimado,
            'Situação': situacao,
            'Data da Abertura': data_abertura,
            'Modalidade': modalidade,
            'Edital': edital_link,
            'Descrição Completa': descricao_completa
        }

    return None

def extract_monetary_value(value):
    match = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?)', value)
    return match.group(1) if match else 'Não encontrado'

def extract_data_from_page(page_url):
    response = requests.get(page_url)
    if response.status_code == 200:
        page_soup = BeautifulSoup(response.text, 'html.parser')
        lista_div = page_soup.find('div', class_='lista-template-licitacao')

        if lista_div:
            span12_blocks = lista_div.find_all('div', class_='span12')
            extracted_data = []

            for block in span12_blocks:
                date_elem = block.find('small', class_='muted')
                date = date_elem.text.strip() if date_elem else 'Data não encontrada'

                title_elem = block.find('span', class_='title')
                title = title_elem.text.strip() if title_elem else 'Título não encontrado'
                link = title_elem.find('a')['href'] if title_elem and title_elem.find('a') else 'Link não encontrado'

                additional_info = extract_additional_info(link)

                reordered_info = {
                    'Id': additional_info.get('Id', 'Não encontrado'),
                    'Data da Publicação': date,
                    'Título': title,
                    'Link': link,
                    'Unidade Administrativa': additional_info.get('Unidade Administrativa', 'Não encontrada'),
                    'Modalidade': additional_info.get('Modalidade', 'Não encontrada'),
                    'Valor Estimado': additional_info.get('Valor Estimado', 'Não encontrado'),
                    'Situação': additional_info.get('Situação', 'Não encontrada'),
                    'Data da Abertura': additional_info.get('Data da Abertura', 'Não encontrada'),
                    'Edital': additional_info.get('Edital', 'Não encontrado'),
                    'Descrição Completa': additional_info.get('Descrição Completa', 'Não encontrada')
                }

                extracted_data.append(reordered_info)

            return extracted_data

    return None

# Defina a URL da página inicial
page_url = "https://rondonia.ro.gov.br/supel/licitacoes/"

# Loop até que a menor data de publicação seja menor que hoje
while True:
    extracted_data = extract_data_from_page(page_url)

    if not extracted_data:
        break

    # Atualize a página para a próxima página
    match = re.search(r'/pg/(\d+)/', page_url)
    if not match:
        break

    page_number = int(match.group(1))
    next_page_url = "https://rondonia.ro.gov.br/supel/licitacoes/pg/{}/".format(page_number + 1)

    # Verifique a menor data de publicação
    min_date = min(item['Data da Publicação'] for item in extracted_data)
    min_date_obj = datetime.strptime(min_date, '%d/%m/%Y').date()

    if min_date_obj >= datetime.now().date():
        break

    page_url = next_page_url


# Agora, 'extracted_data' contém os dados de todas as páginas até a menor data cadastral ser menor que hoje
json_data = json.dumps(extracted_data, ensure_ascii=False, indent=2)
print(json_data)
