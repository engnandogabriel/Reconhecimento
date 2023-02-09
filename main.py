
import face_recognition
import cv2
import numpy as np
import funcoes

captura = cv2.VideoCapture(0)

facesConhecidas = funcoes.ImportarFaces()
nomesFacesConhecidas = funcoes.ImportarNomes()
matriculas = funcoes.ImportarMatriculas()
continuarProcesso = True

while True:
    ret, frame = captura.read()

    if continuarProcesso:
        
        frameFormatado = funcoes.TratarFrame(frame)
        
        localizacaoFaces = face_recognition.face_locations(frameFormatado)
        faces = face_recognition.face_encodings(frameFormatado, localizacaoFaces)

        nomesFaces = []
        for face in faces:
            correspondem = face_recognition.compare_faces(facesConhecidas, face, tolerance=0.5)
            nome = "Não Registrado"

            if True in correspondem:
                primeiraCorrespondencia = correspondem.index(True)
                nome = nomesFacesConhecidas[primeiraCorrespondencia]
                

            nomesFaces.append(nome)

    continuarProcesso = not continuarProcesso

    for (cima, direita, baixo, esquerda), nome in zip(localizacaoFaces, nomesFaces):
        cima *= 4
        direita *= 4
        baixo *= 4
        esquerda *= 4

        cv2.rectangle(frame, (esquerda, cima), (direita, baixo), (255, 255, 0), 3)

        cv2.rectangle(frame, (esquerda, baixo - 35), (direita, baixo), (255, 255, 0), cv2.FILLED)
        fonte = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, nome, (esquerda + 6, baixo - 6), fonte, 1.0, (255, 255, 255), 1)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
captura.release()
cv2.destroyAllWindows()