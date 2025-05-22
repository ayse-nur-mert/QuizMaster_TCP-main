import json
import socket
import random
import sys

# Joker (Sunucu) uygulaması
class JokerServer:
    def __init__(self, host='127.0.0.1', port=4338):
        """
        Joker sunucusunu başlatır ve gerekli soket bağlantısını oluşturur.
        Host ve port değerlerini ayarlar, sunucu soketi oluşturur ve dinlemeye başlar.
        """
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f'Joker sunucu {self.host}:{self.port} adresinde dinliyor.')
        self.running = True

    def accept_program_server(self):
        """
        Program sunucusundan gelen bağlantı isteğini kabul eder.
        Bağlantıyı oluşturur ve soket nesnesini döndürür.
        """
        program_socket, program_address = self.server_socket.accept()
        print(f'Bağlantı kabul edildi: {program_address}')
        return program_socket

    def process_joker_request(self, program_socket):
        """
        Program sunucusundan gelen joker isteğini işler.
        İstek türüne göre uygun joker fonksiyonunu çağırır ve sonucu döndürür.
        Kapatma isteği gelirse sunucuyu kapatmak için False döndürür.
        """
        try:
            request_data = program_socket.recv(1024).decode()
            request = json.loads(request_data)
            
            joker_type = request.get("joker_type")
            
            # Kapatma isteği kontrolü
            if joker_type == "shutdown":
                message = request.get("message", "Joker sunucusu kapatılıyor.")
                print(message)
                program_socket.sendall("Joker sunucusu kapatılıyor.".encode())
                self.running = False
                return False
            
            question = request.get("question")
            options = request.get("options")
            correct_answer = request.get("answer")
            
            if joker_type == "seyirci":
                response = self.audience_joker(options, correct_answer)
            elif joker_type == "yariyariya":
                response = self.fifty_fifty_joker(options, correct_answer)
            else:
                response = "Geçersiz joker tipi"
                
            program_socket.sendall(response.encode())
            return True
            
        except Exception as e:
            print(f'Joker isteği işleme hatası: {e}')
            program_socket.sendall("Joker işleme hatası".encode())
            return True

    def audience_joker(self, options, correct_answer):
        """
        Seyirciye Sorma jokeri işlevini gerçekleştirir.
        Doğru cevap için daha yüksek bir yüzde belirler ve diğer seçeneklere
        kalan yüzdeyi rastgele dağıtır. Seyirci tahminlerini şekillendirir.
        """
        percentages = {}
        remaining = 100
        
        # Doğru cevaba %40-60 arası bir değer ver
        correct_percentage = random.randint(40, 60)
        percentages[correct_answer] = correct_percentage
        remaining -= correct_percentage
        
        # Diğer seçeneklere kalan yüzdeyi dağıt
        other_options = [opt for opt in options.keys() if opt != correct_answer]
        for i, option in enumerate(other_options):
            if i == len(other_options) - 1:
                percentages[option] = remaining
            else:
                percentage = random.randint(5, remaining - 5 * (len(other_options) - i - 1))
                percentages[option] = percentage
                remaining -= percentage
        
        # Cevap metnini oluştur
        response = "Şıklar: "
        for option, text in options.items():
            response += f"{option}) {text} (%{percentages[option]}) "
            
        return response

    def fifty_fifty_joker(self, options, correct_answer):
        """
        Yarı Yarıya joker işlevini gerçekleştirir.
        İki yanlış şıkkı elemek için, doğru cevabı ve rastgele seçilen
        bir yanlış cevabı bırakarak diğerlerini kaldırır.
        """
        # Yanlış cevapları bul
        wrong_options = [opt for opt in options.keys() if opt != correct_answer]
        
        # Rastgele bir yanlış cevap seç
        kept_wrong_option = random.choice(wrong_options)
        
        # Kalan seçenekleri oluştur
        remaining_options = {
            correct_answer: options[correct_answer],
            kept_wrong_option: options[kept_wrong_option]
        }
        
        # Cevap metnini oluştur
        response = "Şıklar: "
        for option in sorted(remaining_options.keys()):
            response += f"{option}) {remaining_options[option]} "
            
        return response

    def close(self):
        """
        Joker sunucusunu kapatır ve soket bağlantısını sonlandırır.
        """
        self.server_socket.close()
        print('Joker sunucu kapatıldı.')

# Örnek kullanım
if __name__ == "__main__":
    joker_server = JokerServer()
    while joker_server.running:
        try:
            program_socket = joker_server.accept_program_server()
            if not joker_server.process_joker_request(program_socket):
                break
        except KeyboardInterrupt:
            print("\nJoker sunucusu kapatılıyor...")
            break
    
    joker_server.close()
    sys.exit(0) 