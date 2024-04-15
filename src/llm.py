import openai
import json
import os 

def resume_news(nota):
	api_key = os.getenv('openai_key')
	openai.api_key = os.getenv('openai_key')
	
	response = openai.ChatCompletion.create(
		model="gpt-3.5-turbo-0613",	
		messages=[
		{"role": "system", "content": "Eres un experto creador de newsletter que impactan"},
		{"role":"user","content": "Crea resumen y título amigable, resumen y título creativo; resumen y título dramático para la siguiente nota: " + nota + "; el título debera ser de 15 palabras y el resumen de 35 palabras en español; el resumen deberá tener una intención a seguir leyendo la noticia; el resultado debe estar en el siguiente formato Json {""titulo_amigable"": ""valor"", ""resumen_amigable"": ""valor"", ""titulo_creativo"": ""valor"", ""resumen_creativo"": ""valor"", ""titulo_dramatico"": ""valor"", ""resumen_dramatico"": ""valor""}   "},
		],
		#n=3
		temperature=0.8
		)

	print(response["choices"][0]["message"]["content"])
	datos = json.loads(response["choices"][0]["message"]["content"])
	
	titulos = ''
	resumenes = ''
	
	for key in datos.keys():		
	    if 'titulo' in key:
	        titulos += datos[key] + '|'
	    elif 'resumen' in key:
	        resumenes += datos[key] + '|'
	titulos = titulos[:-1]
	resumenes = resumenes[:-1]

	return resumenes, titulos