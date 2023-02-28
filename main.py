#IMPORTANTE: A maior parte do funcionamento desse código foi retirado do repositório da própria biblioteca no github: https://github.com/ageitgey/face_recognition
#O código foi adaptado para o português afim de melhorar a legibilidade
#OBS: Para encerrar o programa, basta apertar a tecla Q

import face_recognition #Responsável por fazer o reconhecimento facial
import cv2 #Usada para acessar a câmera
import funcoes #Onde contém as funções específicas do código

captura = cv2.VideoCapture(0) #Inicia a câmera

facesConhecidas = funcoes.ImportarFaces() #Armazena as faces que já estavam salvas localmente
nomesFacesConhecidas = funcoes.ImportarNomes() #Armazena, com os mesmos índices da lista anterior, os nomes dos alunos
matriculas = funcoes.ImportarMatriculas() #Armazena, com os mesmos índices da lista anterior, as matrículas dos alunos

# ter controle se o aluno já foi verificado
controleData = []
controleBanco = [] 
for c in range(len(matriculas)):
    controleData.append(0)
    controleBanco.append(0)


continuarProcesso = True #Variável de controle

while True:

    ret, frame = captura.read() #Leitura do frame da camera

    if continuarProcesso:
        
        frameFormatado = funcoes.TratarFrame(frame)
        
        #Localiza e extrai as faces do frame que foi lido pela câmera
        localizacaoFaces = face_recognition.face_locations(frameFormatado)
        faces = face_recognition.face_encodings(frameFormatado, localizacaoFaces)

        nomesFaces = [] #Lista que armazena os nomes das pessoas que foram reconhecidas pela câmera

        #Esse processo é feito para cada pessoa reconhecida pela câmera:
        for face in faces:
            #Procura a face em questão na lista de faces registradas e caso seja encontrada, adiciona o nome correspondente (da lista de nomes conhecidos) na lista de nomes acima
            correspondem = face_recognition.compare_faces(facesConhecidas, face, tolerance=0.5) #A tolerancia padrão é 0.6, por isso, algumas vezes, 
            #pode acabar não reconhecendo a pessoa, mas é por um breve tempo. A tolerância base estava confundindo as faces, por isso a mudança
            nome = "Desconhecido" #Caso a pessoa não seja encontrada, esse será o nome que aparecerá para ela

            if True in correspondem:
                primeiraCorrespondencia = correspondem.index(True)
                nome = nomesFacesConhecidas[primeiraCorrespondencia]
                matricula = matriculas[primeiraCorrespondencia]


                if (controleBanco[primeiraCorrespondencia] == 0):
                    controleBanco[primeiraCorrespondencia] = funcoes.verificaPresenca(primeiraCorrespondencia)
                    if controleBanco[primeiraCorrespondencia] == 1:
                        print('Aluno ja registrado')
                    

                if controleData[primeiraCorrespondencia] == 0:
                    if controleBanco[primeiraCorrespondencia] == 0:
                        print('Registrando Aluno')
                        funcoes.ConfirmaPresenca(primeiraCorrespondencia,nome, matricula, controleData)
                        controleData[primeiraCorrespondencia] = 1
                        controleBanco[primeiraCorrespondencia] = 1
                        
            # print("Controle banco {}".format(controleBanco[primeiraCorrespondencia]))
            nomesFaces.append(nome)

    continuarProcesso = not continuarProcesso #Dá um tempo para que o processamento possa ocorrer.

    #Cria um quadrado ao redor do rosto das pessoas com seus respectivos nomes abaixo. Se a pessoa não for reconhecida, vai mostrar "Não Registrado"
    for (cima, direita, baixo, esquerda), nome in zip(localizacaoFaces, nomesFaces):
        cima *= 4
        direita *= 4
        baixo *= 4
        esquerda *= 4

        cv2.rectangle(frame, (esquerda, cima), (direita, baixo), (255, 255, 0), 3) #Configurações do quadrado maior
        cv2.rectangle(frame, (esquerda, baixo - 35), (direita, baixo), (255, 255, 0), cv2.FILLED) #Configurações do retângulo
        fonte = cv2.FONT_HERSHEY_DUPLEX
        if nome == 'Desconhecido':
            cv2.putText(frame, nome, (esquerda + 6, baixo - 6), fonte, 1.0, (0, 0, 255), 1) #Configurações do texto
        else:
            cv2.putText(frame, nome, (esquerda + 6, baixo - 6), fonte, 1.0, (0, 0, 0), 1) #Configurações do texto

    cv2.imshow('Video', frame) #Mostra a câmera na tela

    #Apertar a tecla Q encerra a câmera, como dito no início
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
#Encerra o código
captura.release()
cv2.destroyAllWindows()