#Desenvolvido por Rafael Nascimento de Sousa, graduando em Engenharia da Computação, IFMA - Campus Santa Inês em fevereiro de 2023

import face_recognition #Responsável por fazer o reconhecimento facial
import numpy as np #Usada para trabalhar com vetores de múltiplas dimensões
import base64 #Usada para converter um vetor complexo em uma string sem perda de informações
import requests #Usada para fazer requisições ao servidor
import urllib.request #Usada para fazer os downloads necessários
import cv2 #Usada para acessar a câmera
import datetime  #Usada para pegar a data atual 


aSeremRegistrados = {} #Dicionário de dicionários -> Chave: id do aluno do banco de dados; Valor: Dicionário contendo as informações do aluno
aSeremAtualizados = {} #Dicionário de dicionários -> Chave: id do aluno no banco de dados; Valor :Dicionário contendo as informações do aluno
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
            aSeremRegistrados[registro['_id']] = {'nome' : registro['nome'], 'matricula' : registro['matricula'], 'foto' : registro['foto']}
    if len(aSeremRegistrados) == 0: #Se houver algum aluno salvo no dicionário, significa que é necessária uma atualização no banco local
        print('Nenhum aluno a ser cadastrado!')
        return False
    
    print('{} a ser registrado'.format(len(aSeremRegistrados)))
    return True
    
def verificaAtualizacao():
    for atualizacao in requisicao.json():
        if atualizacao['atualized'] == True:
            aSeremAtualizados[atualizacao['_id']] = {'nome' : atualizacao['nome'], 'matricula' : atualizacao['matricula'], 'foto' : atualizacao['foto']}
    if len(aSeremAtualizados) == 0:
        print('Nenhum aluno a ser atualizado')
        return False
    
    print('{} a ser atualizado' .format(len(aSeremAtualizados)))
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
    print(matriculas)
    return matriculas

#método para atualizar aluno
def atualizarAluno(matricula, face):

    backup = np.load(faces_armazenadas)

    faces = [] #Lista que vai armazenar todos os códigos faciais 

    #Armazena na lista de faces todas os objetos (faces) não nulas que estão na variável de backup
    for item in backup.files:
        if backup[item] != []: #Verifica se o objeto não é vazio. Essa verificação é feita para o caso do try..except acima.
            faces.append(backup[item]) 

    matriculasAlunos = ImportarMatriculas()
    
    for c in range(len(matriculasAlunos)):
        if matriculasAlunos[c] == matricula:
            print(matriculasAlunos[c])
            index = c
            break 
    
    faces[index] = face   
    np.savez(faces_armazenadas, *faces) #Salva a lista de faces (atualizada com a nova) no arquivo .npz

    tobase64 = base64.b64encode(face) #Converte a face para uma string codificada usando base64.

    #Atualiza o servidor com os códigos faciais em base64 e atualiza a informação de que o aluno agora já tem seu código facial cadastrado
    requests.patch("{}/atualized/id/{}".format(api, matricula), {'atualized' : False})
    requests.patch("{}/id/{}".format(api,matricula), {'caracteres' : tobase64})
    # /atualized/id/:matricula

# método para verificar se o aluno já foi registrado a frequência
def verificaPresenca(id):
    
    # Requisição para recuperar a presença do usuário
    #get = requests.get("%s/id/%s"%(api, matricula)).json()
    get = requisicao.json()[id]
    print('ID {}'.format(id))
    print(get)
    
    
    frequencia = get['frequencia']
    tamanhoFrequencia = len(frequencia)
    
    print('Tamanho Ultima frequencia: {}'.format(len(frequencia)))

    if(len(frequencia) != 0):
        ultimaFrequenica = frequencia[tamanhoFrequencia-1]
        ultimaFrequenica = ultimaFrequenica.split('T')[0]
    else:
        ultimaFrequenica = '0000-00-00'
    # print('ultimaFrequenica: {}'.format(ultimaFrequenica))
    
    dateDatabase = get['atualizedAt']

    # Seperar o date da requisição do usuário e recuperar apenas a data 
    dateUser = dateDatabase.split('T')
    dateUser = dateUser[0]
    print(dateUser)
    
    #converter dcurrentDate para string
    currentDate = datetime.date.today() #recupera o dia atual 
    currentDate = currentDate.strftime('%Y-%m-%d') #converter para string
    print('currentDate: {}'.format(currentDate))

    #se o campo frequencia estiver vazio, cadastrar frequencia mesmo se a data do BD for igual a data atual,
    #pois isso significa que o usuário foi cadastrado no mesmo dia em que ele começou a usar o sistema

    if (len(frequencia) == 0):
        print('Cadastro de frequência')
        return 0
    
    elif(ultimaFrequenica == currentDate):
        print('Cadastro de frequência já realizado')
        return 1

    #if a data do DB for diferente da data atual, significa que o usuário ja foi registrado no BD
    elif dateUser == currentDate:
        print('Cadastro de frequência já realizado')
        return 1
        
    #caso as duas condições forem falsas, registrar usuário no BD
    else:
        print('Cadastro de frequência')
        return 0

#Esse é um método que ainda deve ser implementado. Deve ser acionado quando o aluno for reconhecido. Depende do funcionamento interno de registro de presença do Campus
def ConfirmaPresenca(id, nome, matricula,contoledata):

    print("Registrando o usuário %s com matricula %s no bando de dados"%(nome,matricula))

    print(contoledata[id])

    # Requisição para recuperar a presença do usuárioq
    get = requisicao.json()[id]
    dateDatabase = get['atualizedAt']
    frequencia = get['frequencia']
    tamanhoFrequencia = len(frequencia)
    
    print('Tamanho Ultima frequencia: {}'.format(len(frequencia)))

    if(len(frequencia) != 0):
        ultimaFrequenica = frequencia[tamanhoFrequencia-1]
        ultimaFrequenica = ultimaFrequenica.split('T')[0]
    else:
        ultimaFrequenica = '0000-00-00'
    
    # Seperar o date da requisição e recuperar apenas a data do usuario
    dateUser = dateDatabase.split('T')[0]
    print(dateUser)

    #data que sera registrado no banco de dados no campo frequencia
    currentDate = datetime.datetime.now()
    currentDate = currentDate.strftime('%Y-%m-%dT%H:%M')

    #data que vai ser registrado no banco de dados no campo atualizedAt
    currentDataBase = datetime.datetime.now()


    # se a data de hoje for diferente da data do usuário:
    # if (ultimaFrequenica == currentDate):
    if currentDate != dateUser:
        requests.patch("%s/registrarfrequencia/%s"%(api, matricula), {'atualizedAt' : currentDataBase, 'dateUser': currentDate})
        print("Aluno registrado com suscesso")
        return 1


#Essa função serve apenas para deixar os frames da câmera mais facilmente processados.
def TratarFrame(frame):
    frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25) #Reduz o tamanho do Frame para aprimorar performance
    frame = frame[:, :, ::-1] #Altera o padrão de cores de bgr para rgb
    return frame

def main():
    #Se houver necessidade de cadastro, a rotina é acionada
    if VerificaRegistro():
        #Extrai a face de cada aluno que deve ser atualizado e faz seu armazenamento
        for registro in aSeremRegistrados:
            face = ExtrairFace(aSeremRegistrados[registro]['foto'], aSeremRegistrados[registro]['matricula'])
            ArmazenarFace(aSeremRegistrados[registro], face)

    #Se houver nescessidade de atualização, a rotina é acionada
    if verificaAtualizacao():
        for atualizacao in aSeremAtualizados:

            face = ExtrairFace(aSeremAtualizados[atualizacao]['foto'], aSeremAtualizados[atualizacao]['matricula'])
            atualizarAluno(aSeremAtualizados[atualizacao]['matricula'], face)

main()