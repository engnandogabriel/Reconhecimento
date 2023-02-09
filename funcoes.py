#Desenvolvido por Rafael Nascimento de Sousa, graduando em Engenharia da Computação, IFMA - Campus Santa Inês em fevereiro de 2023

import face_recognition #Responsável por fazer o reconhecimento facial
import numpy as np #Usada para trabalhar com vetores de múltiplas dimensões
import base64 #Usada para converter um vetor complexo em uma string sem perda de informações
import requests #Usada para fazer requisições ao servidor
import urllib.request #Usada para fazer os downloads necessários
import cv2 #Usada para acessar a câmera

aSeremRegistrados = {} #Dicionário de dicionários -> Chave: id do aluno do banco de dados; Valor: Dicionário contendo as informações do aluno
api = "https://api-fapema.herokuapp.com/reconhecimento"
faces_armazenadas = "data/backup/faces.npz" #Caminho do backup local dos códigos faciais
requisicao = requests.get(api) #Variável que recebe o banco de dados como um dicionário


#Faz o Download das imagens dos alunos 
#Parâmetros: string do link da foto, string com a matrícula do aluno | Retorna o caminho da imagem
def ImportarImagem(link, matricula):
    caminhoDaImagem = "data/imagens/%s.jpg"%matricula #String contendo o caminho onde a imagem será armazenada
    urllib.request.urlretrieve(link, caminhoDaImagem) #Download
    return caminhoDaImagem 

#Extrai os códigos faciais (face) da foto do aluno 
#Parâmetros: string do link da foto, string com a matrícula do aluno | Retorna a face
def ExtrairFace(link, matricula):
    imagem = ImportarImagem(link, matricula) #Armazena o caminho da foto na variável
    aluno = face_recognition.load_image_file(imagem) #Carrega a imagem para o código
    face = face_recognition.face_encodings(aluno)[0] #Extrai, de fato, a face da imagem carregada
    return face

#Armazena o código facial e o nome do aluno localmente, e envia o código facial dele para o servidor
#Parâmetros: dicionário contendo todos os dados do aluno, código facial do aluno
def ArmazenarFace(registro, face):
    
    #ARMAZENAMENTO LOCAL:

    #Tenta-se carregar o arquivo de faces local, onde todas as faces estão armazenadas
    #Caso o arquivo não exista, cria-se o arquivo e em seguida, ele é carregado
    #O arquivo é carregado para não haver sobreposição
    try:
        backup = np.load(faces_armazenadas) #As faces ficarão em um dicionário base do numpy. Para mais informações pesquise sobre o np.load em arquivos .npz
    except:
        np.savez(faces_armazenadas, np.array([])) #Cria-se um arquivo .npz que armazena apenas um array vazio que DEVE ser removido a seguir
        backup = np.load(faces_armazenadas)

    faces = [] #Lista que vai armazenar todos os códigos faciais 

    #Armazena na lista de faces todas os objetos (faces) não nulas que estão na variável de backup
    for item in backup.files:
        if backup[item] != []: #Verifica se o objeto não é vazio. Essa verificação é feita para o caso do try..except acima.
            faces.append(backup[item]) 

    faces.append(face) #Adiciona-se a face a ser armazenada (que foi passada como parâmetro) na lista de faces
    np.savez(faces_armazenadas, *faces) #Salva a lista de faces (atualizada com a nova) no arquivo .npz

    #Abaixo adiciona-se o nome e a matrícula dos alunos em um arquivo local no seguinte formato: matricula1:aluno1/matricula2:aluno2/.../matriculaN:alunoN/
    with open("data/backup/nomes.txt", "a") as arquivo:
        arquivo.write("%s:%s/"%(registro['matricula'], registro['nome']))

    #ARMAZENAMENTO DAS FACES NO SERVIDOR:

    tobase64 = base64.b64encode(face) #Converte a face para uma string codificada usando base64.

    #Atualiza o servidor com os códigos faciais em base64 e atualiza a informação de que o aluno agora já tem seu código facial cadastrado
    requests.patch("%s/id/%s"%(api, registro['matricula']), {'caracteres' : tobase64, 'registered' : True})

#Carrega as faces do arquivo local | Retorna uma lista de faces
def ImportarFaces():
    backup = np.load(faces_armazenadas) #Carrega as faces
    faces = [] #Lista que armazenará as faces
    
    #Armazena todas as faces não nulas que estão na variável de backup
    for item in backup.files:
        if backup[item] != []:
            faces.append(backup[item])
    return faces

#Varre o banco de dados e verifica se há algum registro novo | Retorna um boolean
def VerificaRegistro():
    for registro in requisicao.json():
        if registro['registered'] == False: #Salva, no dicionário, os dados de qualquer aluno que ainda não tem face registrada
            aSeremRegistrados[registro['_id']] = {'nome' : registro['nome'], 'matricula' : registro['matricula'], 'foto' : registro['foto'], 'presenca' : registro['presenca']}
    if len(aSeremRegistrados) == 0: #Se houver algum aluno salvo no dicionário, significa que é necessária uma atualização no banco local
        return False
    else:
        return True

#Carrega os nomes do arquivo local | Retorna uma lista com nomes
def ImportarNomes():
    #Carrega o arquivo na variável
    with open("data/backup/nomes.txt", "r") as arquivo:
        texto = arquivo.read()
    arquivo.close()

    nomes = [] #Lista que vai armazenar os nomes
    alunos = texto.split("/") #Divide o arquivo em uma lista com a seguinte estrutura: [matricula1:aluno1, matricula2:aluno2,..., matriculaN:alunoN, NULL]
    alunos.pop() #Remove o valor nulo da última posição da lista
    #Separa cada item da lista alunos em dois: matricula, nome. Em seguida, armazena na variável nomes apenas o nome do aluno
    for aluno in alunos:
        nomes.append(aluno.split(":")[1])
    return nomes

#Faz o mesmo processo da função anterior, mas agora com a matrícula. Serve se uma lista de matrículas for necessária. Pode ser usada para a mesma finalidade da lista de nomes
def ImportarMatriculas():
    with open("data/backup/nomes.txt", "r") as arquivo:
        texto = arquivo.read()
    arquivo.close()
    matriculas = [] 
    alunos = texto.split("/")
    alunos.pop()
    for aluno in alunos:
        matriculas.append(aluno.split(":")[0])
    return matriculas

#Esse é um método que ainda deve ser implementado. Deve ser acionado quando o aluno for reconhecido. Depende do funcionamento interno de registro de presença do Campus
def ConfirmaPresenca(matricula):
    pass

#Essa função serve apenas para deixar os frames da câmera mais facilmente processados.
def TratarFrame(frame):
    frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25) #Reduz o tamanho do Frame para aprimorar performance
    frame = frame[:, :, ::-1] #Altera o padrão de cores de bgr para rgb
    return frame

#Se houver necessidade de atualização, a rotina é acionada
if VerificaRegistro():
    #Extrai a face de cada aluno que deve ser atualizado e faz seu armazenamento
    for registro in aSeremRegistrados:
        face = ExtrairFace(aSeremRegistrados[registro]['foto'], aSeremRegistrados[registro]['matricula'])
        ArmazenarFace(aSeremRegistrados[registro], face)

