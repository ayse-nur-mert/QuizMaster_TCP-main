import json
import socket
import time
import random  # Import the random module
import sys  # Import sys module for command line arguments

# JSON dosyasından soruları yükle
with open('questions.json', 'r') as file:
    questions_data = json.load(file)

# Soruları seviyelerine göre grupla ve her seviyeden rastgele seç
def select_random_questions(questions_data, questions_per_level=1):
    """
    Her seviyeden belirtilen sayıda rastgele soru seçer ve seviyelere göre sıralar.
    Her seviye için ayrı bir soru grubu oluşturur ve bu gruplardan rastgele seçim yapar.
    """
    # Soruları seviyelerine göre grupla
    questions_by_level = {}
    for question in questions_data['questions']:
        level = question['level']
        if level not in questions_by_level:
            questions_by_level[level] = []
        questions_by_level[level].append(question)
    
    # Her seviyeden rastgele soru seç
    selected_questions = []
    for level in sorted(questions_by_level.keys()):
        # Mevcut soruların sayısıyla sınırla
        num_to_select = min(questions_per_level, len(questions_by_level[level]))
        selected = random.sample(questions_by_level[level], num_to_select)
        selected_questions.extend(selected)
    
    # Soruları seviyelerine göre sırala (rastgele karıştırmak yerine)
    selected_questions.sort(key=lambda q: q['level'])
    
    return selected_questions

# Program Sunucusu (Sunucu-İstemci) uygulaması
class ProgramServer:
    def __init__(self, host='127.0.0.1', port=4337, joker_host='127.0.0.1', joker_port=4338):
        """
        Program sunucusunu başlatır ve gerekli soket bağlantılarını oluşturur.
        Ana sunucu ve joker sunucusu için host ve port değerlerini ayarlar.
        """
        self.host = host
        self.port = port
        self.joker_host = joker_host
        self.joker_port = joker_port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f'Sunucu {self.host}:{self.port} adresinde dinliyor.')

    def accept_client(self):
        """
        İstemci bağlantı isteğini kabul eder ve bağlantıyı geri döndürür.
        """
        client_socket, client_address = self.server_socket.accept()
        print(f'Bağlantı kabul edildi: {client_address}')
        return client_socket

    def send_question(self, client_socket, question):
        """
        İstemciye soruyu gönderir. 
        Soruyu byte dizisine çevirir ve istemciye iletir.
        """
        try:
            client_socket.sendall(question.encode())
        except Exception as e:
            print(f'Soru gönderme hatası: {e}')

    def receive_answer(self, client_socket):
        """
        İstemciden cevabı alır.
        Gelen byte dizisini çözümleyip string olarak döndürür.
        """
        try:
            answer = client_socket.recv(1024).decode()
            return answer
        except Exception as e:
            print(f'Cevap alma hatası: {e}')
            return None
            
    def use_joker(self, joker_type, question_data):
        """
        Belirtilen joker tipini kullanır ve joker sunucusundan sonuç alır.
        Soru bilgilerini joker sunucusuna gönderir ve cevabı döndürür.
        """
        try:
            # Joker sunucusuna bağlan
            joker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            joker_socket.connect((self.joker_host, self.joker_port))
            
            # Joker isteği gönder
            request = {
                "joker_type": joker_type,
                "question": question_data["question"],
                "options": question_data["options"],
                "answer": question_data["answer"]
            }
            joker_socket.sendall(json.dumps(request).encode())
            
            # Joker cevabını al
            response = joker_socket.recv(1024).decode()
            joker_socket.close()
            
            return response
        except Exception as e:
            print(f'Joker kullanım hatası: {e}')
            return "Joker sunucusuyla bağlantı kurulamadı."
            
    def shutdown_joker_server(self):
        """
        Joker sunucusunu kapatır.
        Kapatma isteğini gönderir ve sunucunun kapanmasını bekler.
        """
        try:
            # Joker sunucusuna bağlan
            joker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            joker_socket.connect((self.joker_host, self.joker_port))
            
            # Kapatma isteği gönder
            print("Joker sunucusuna kapatma isteği gönderiliyor...")
            request = {
                "joker_type": "shutdown",
                "message": "Yarışma sona erdi, joker sunucusu kapatılıyor."
            }
            joker_socket.sendall(json.dumps(request).encode())
            
            # Joker sunucusunun yanıtını al
            response = joker_socket.recv(1024).decode()
            print(f"Joker sunucusu yanıtı: {response}")
            joker_socket.close()
            
            # Joker sunucusunun kapanması için kısa bir süre bekle
            time.sleep(0.5)
        except Exception as e:
            print(f'Joker sunucusu kapatma hatası: {e}')

    def close(self):
        """
        Sunucu soketini kapatır ve programı sonlandırır.
        """
        try:
            self.server_socket.close()
            print('Sunucu kapatıldı.')
        except Exception as e:
            print(f'Sunucu kapatma hatası: {e}')

# Örnek kullanım
if __name__ == "__main__":
    # Komut satırından soru sayısı alınabilir
    questions_per_level = 1  # Varsayılan değer
    
    if len(sys.argv) > 1:
        try:
            questions_per_level = int(sys.argv[1])
            print(f"Her seviyeden {questions_per_level} soru seçilecek")
        except ValueError:
            print("Geçersiz soru sayısı. Varsayılan olarak her seviyeden 1 soru seçilecek.")
    
    server = ProgramServer()
    client_socket = server.accept_client()
    
    # Ödül mesajları
    reward_messages = [
        "Linç Yükleniyor",
        "Önemli olan katılmaktı",
        "İki birden büyüktür",
        "Buralara kolay gelmedik",
        "Sen bu işi biliyorsun",
        "Harikasın"
    ]
    
    # Joker hakları
    available_jokers = {"S": True, "Y": True}
    
    # Her seviyeden belirtilen sayıda soru seç
    selected_questions = select_random_questions(questions_data, questions_per_level)
    
    try:
        # Seçilen soruları sor
        for index, question_data in enumerate(selected_questions):
            # Joker bilgisi ile soru metnini hazırla
            joker_text = ""
            if available_jokers["S"] or available_jokers["Y"]:
                joker_text = "\nJokerler: "
                if available_jokers["S"]:
                    joker_text += "Seyirciye Sorma (S), "
                if available_jokers["Y"]:
                    joker_text += "Yarı Yarıya (Y)"
                joker_text = joker_text.rstrip(", ")
            
            # Seviyeyi soruya ekle
            question_text = f"{index + 1}. Soru (Seviye {question_data['level']}): {question_data['question']}\nŞıklar: "
            for option, text in question_data['options'].items():
                question_text += f"{option}) {text} "
            
            question_text += joker_text
            question_text += "\nCevabınızı girin (A, B, C, D)"
            if available_jokers["S"] or available_jokers["Y"]:
                question_text += " veya Joker kullanın (S, Y)"
            question_text += ": "
            
            server.send_question(client_socket, question_text)
            answer = server.receive_answer(client_socket)
            
            if answer:
                # Joker kullanımı
                if answer.upper() == "S" and available_jokers["S"]:
                    available_jokers["S"] = False  # Seyirciye Sorma jokerini kullan
                    joker_response = server.use_joker("seyirci", question_data)
                    
                    # Joker cevabını gönder
                    joker_question_text = f"{index + 1}. Soru (Seviye {question_data['level']}): {question_data['question']}\n{joker_response}\nCevabınızı girin (A, B, C, D): "
                    server.send_question(client_socket, joker_question_text)
                    answer = server.receive_answer(client_socket)
                    
                elif answer.upper() == "Y" and available_jokers["Y"]:
                    available_jokers["Y"] = False  # Yarı Yarıya jokerini kullan
                    joker_response = server.use_joker("yariyariya", question_data)
                    
                    # Joker cevabını gönder
                    joker_question_text = f"{index + 1}. Soru (Seviye {question_data['level']}): {question_data['question']}\n{joker_response}\nCevabınızı girin: "
                    server.send_question(client_socket, joker_question_text)
                    answer = server.receive_answer(client_socket)
                
                # Joker hakkı olmadan joker kullanmaya çalışırsa
                elif answer.upper() == "S" and not available_jokers["S"]:
                    server.send_question(client_socket, "Seyirciye Sorma jokeri hakkınız kalmadı. Lütfen bir cevap girin (A, B, C, D): ")
                    answer = server.receive_answer(client_socket)
                    
                elif answer.upper() == "Y" and not available_jokers["Y"]:
                    server.send_question(client_socket, "Yarı Yarıya jokeri hakkınız kalmadı. Lütfen bir cevap girin (A, B, C, D): ")
                    answer = server.receive_answer(client_socket)
                
                # Cevap kontrolü
                if answer and answer.upper() == question_data['answer']:
                    print("Doğru cevap!")
                    if index == len(selected_questions) - 1:
                        # Tüm sorular doğru cevaplandı
                        server.send_question(client_socket, reward_messages[index + 1])  # En yüksek ödül mesajı
                        # Başarıyla tamamlandı, artık çıkabiliriz
                        break
                else:
                    print("Yanlış cevap. Doğru cevap: ", question_data['answer'])
                    # Yanlış cevap verildiğinde, o ana kadar doğru cevaplanan soru sayısına göre ödül mesajı gönder
                    server.send_question(client_socket, reward_messages[index])
                    break  # Yanlış cevap verildiğinde döngüden çık
            else:
                print('Cevap alınamadı.')
                break  # Bağlantı kesilirse döngüden çık
    except Exception as e:
        print(f"Hata oluştu: {e}")
    finally:
        try:
            # İstemciye kapanış sinyali gönder
            server.send_question(client_socket, "Program sonlandırılıyor.")
            # Kısa bir süre bekle
            time.sleep(0.5)
            # Joker sunucusunu kapat
            server.shutdown_joker_server()
            # Sunucuyu kapat
            server.close()
        except Exception as e:
            print(f"Kapatma sırasında hata: {e}")
        
        print("Program sonlandırıldı.")
        exit()  # Çıkış yap 