import face_recognition #Responsável por fazer o reconhecimento facial
import numpy as np #Responsável por manipular números de formas diferentes
import base64
import requests
import urllib.request
import cv2

aSeremRegistrados = {}
aSeremRemovidos = {}
api = "https://api-fapema.herokuapp.com/reconhecimento" #Link da API
requisicao = requests.get(api) #Variável que recebe o banco de dados como um dicionário

def ImportarImagem(link, matricula):
    caminhoDaImagem = "data/imagens/%s.jpg"%matricula
    urllib.request.urlretrieve(link, caminhoDaImagem)
    return caminhoDaImagem

def ExportarFace(link, matricula):
    imagem = ImportarImagem(link, matricula)
    aluno = face_recognition.load_image_file(imagem)
    face = face_recognition.face_encodings(aluno)[0]
    return face

def ArmazenarFace(registro, face):
    
    try:
        faces = np.load('data/backup/faces.npz')
    except:
        np.savez('data/backup/faces.npz', np.array([]))
        faces = np.load('data/backup/faces.npz')

    faces_backup = []

    for item in faces.files:
        if faces[item] != []:
            faces_backup.append(faces[item])   
    faces_backup.append(face)
    np.savez('data/backup/faces.npz', *faces_backup)


    tobase64 = base64.b64encode(face) #Criando o arquivo base64 
    #Exporta o base64 para o servidor
    
    
    completo = {'caracteres' : tobase64, 'registered' : True}

    patch = requests.patch("%s/id/%s"%(api, registro['matricula']), completo)

    #Abaixo adiciona-se o nome e o ID dos alunos em um arquivo local
    with open("data/backup/nomes.txt", "a") as arquivo:
        arquivo.write("%s:%s/"%(registro['matricula'], registro['nome']))
    
def ImportarFaces():
    faces = np.load("data/backup/faces.npz")
    faces_backup = []
    for item in faces.files:
        if faces[item] != []:
            faces_backup.append(faces[item])
    return faces_backup

def VerificaRegistro():
    for registro in requisicao.json():
        if registro['registered'] == False:
            aSeremRegistrados[registro['_id']] = {'nome' : registro['nome'], 'matricula' : registro['matricula'], 'foto' : registro['foto'], 'presenca' : registro['presenca']}
    if len(aSeremRegistrados) == 0:
        print('Nenhum aluno a ser registrado')
        return False
    else:
        return True

def ImportarNomes():
    with open("data/backup/nomes.txt", "r") as arquivo:
        texto = arquivo.read()
    arquivo.close()

    nomes = []
    alunos = texto.split("/")
    alunos.pop()
    for aluno in alunos:
        nomes.append(aluno.split(":")[1])


    return nomes

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

    
def ConfirmaPresenca(matricula):
    get = requests.get("%s/id/%s"%(api, matricula))
    json = {'presenca' : get['presenca']+1}
    requests.patch("%s/id/%s"%(api, matricula), json)

def TratarFrame(frame):
    frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25) #Reduz o tamanho do Frame para aprimorar performance
    frame = frame[:, :, ::-1] #Altera o padrão de cores para rgb
    return frame


if VerificaRegistro():
    for registro in aSeremRegistrados:
        face = ExportarFace(aSeremRegistrados[registro]['foto'], aSeremRegistrados[registro]['matricula'])
        ArmazenarFace(aSeremRegistrados[registro], face)

