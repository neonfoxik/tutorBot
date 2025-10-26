import uuid
import requests
import json
import os
from django.conf import settings
from decimal import Decimal


class YooKassaClient:
    """Клиент для работы с API ЮKassa"""
    
    def __init__(self):
        import logging
        logger = logging.getLogger('bot')
        logger.info("Инициализация YooKassa клиента")
        logger.info(f"LOCAL: {os.getenv('LOCAL')}")
        logger.info(f"DEBUG: {settings.DEBUG}")
        
        self.shop_id = settings.YOOKASSA_SHOP_ID
        if not self.shop_id:
            logger.error("YOOKASSA_SHOP_ID не установлен")
        
        self.secret_key = settings.YOOKASSA_SECRET_KEY
        if not self.secret_key:
            logger.error("YOOKASSA_SECRET_KEY не установлен")
        
        self.test_mode = settings.YOOKASSA_TEST_MODE
        logger.info(f"YOOKASSA_TEST_MODE: {self.test_mode}")
        
        # URL для API ЮKassa (одинаковый для тестового и боевого режима)
        self.base_url = "https://api.yookassa.ru/v3"
        
        self.auth = (self.shop_id, self.secret_key)
        logger.info("YooKassa клиент инициализирован")
    
    def create_payment(self, amount, description, return_url=None, metadata=None):
        """
        Создает платеж в ЮKassa
        
        Args:
            amount (Decimal): Сумма платежа
            description (str): Описание платежа
            return_url (str): URL для возврата после оплаты
            metadata (dict): Дополнительные данные
        
        Returns:
            dict: Ответ от API ЮKassa
        """
        import logging
        logger = logging.getLogger('bot')
        logger.info(f"Создание платежа в YooKassa:")
        logger.info(f"Shop ID: {self.shop_id}")
        logger.info(f"Test Mode: {self.test_mode}")
        logger.info(f"Amount: {amount}")
        logger.info(f"Description: {description}")
        logger.info(f"Return URL: {return_url}")
        logger.info(f"Metadata: {metadata}")
        url = f"{self.base_url}/payments"
        
        payment_data = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url or "https://t.me/"
            },
            "capture": True,
            "description": description,
            "receipt": {
                "customer": {
                    "email": "customer@example.com"  # Обязательное поле для чека
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1.00",
                        "amount": {
                            "value": str(amount),
                            "currency": "RUB"
                        },
                        "vat_code": "1",  # Без НДС
                        "payment_mode": "full_prepayment",  # Полная предоплата
                        "payment_subject": "service"  # Услуга
                    }
                ]
            }
        }
        
        if metadata:
            payment_data["metadata"] = metadata
        
        headers = {
            "Idempotence-Key": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }
        
        try:
            print(f"Отправляем запрос к ЮKassa: {url}")
            print(f"Данные платежа: {json.dumps(payment_data, ensure_ascii=False, indent=2)}")
            
            # Настройки для более надежного соединения
            session = requests.Session()
            
            # Используем более простой подход, как в curl
            try:
                logger.info("Отправляем запрос к ЮKassa...")
                
                # Добавляем User-Agent как в curl
                headers['User-Agent'] = 'YooKassa-Bot/1.0'
                
                # Логируем детали запроса
                logger.info(f"URL: {url}")
                logger.info(f"Headers: {headers}")
                logger.info(f"Auth: {bool(self.auth)}")  # Только факт наличия авторизации
                logger.info(f"Payment Data: {json.dumps(payment_data, ensure_ascii=False)}")
                
                response = session.post(
                    url,
                    auth=self.auth,
                    headers=headers,
                    json=payment_data,
                    timeout=(15, 45)  # Увеличиваем timeout
                )
                
                logger.info(f"✅ Запрос отправлен успешно. Статус: {response.status_code}")
                logger.info(f"Ответ: {response.text[:500]}")  # Логируем только первые 500 символов ответа
                
            except requests.exceptions.SSLError as e:
                error_msg = f"❌ SSL ошибка при подключении к ЮKassa: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except requests.exceptions.ConnectionError as e:
                error_msg = f"❌ Ошибка соединения с ЮKassa: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except requests.exceptions.Timeout as e:
                error_msg = f"❌ Превышено время ожидания ответа от ЮKassa: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)
            except Exception as e:
                error_msg = f"❌ Неожиданная ошибка при работе с ЮKassa: {e}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            print(f"Статус ответа: {response.status_code}")
            print(f"Заголовки ответа: {dict(response.headers)}")
            
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = f"❌ Ошибка API ЮKassa (код {response.status_code}):\n"
                    if 'description' in error_data:
                        error_msg += f"Описание: {error_data['description']}\n"
                    if 'code' in error_data:
                        error_msg += f"Код ошибки: {error_data['code']}\n"
                    if 'parameter' in error_data:
                        error_msg += f"Параметр: {error_data['parameter']}"
                except:
                    error_msg = f"❌ Ошибка API ЮKassa (код {response.status_code}):\n{response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            response.raise_for_status()
            result = response.json()
            print(f"Успешный ответ: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # Проверяем наличие URL для оплаты
            if 'confirmation' in result and 'confirmation_url' in result['confirmation']:
                return {
                    'id': result['id'],
                    'confirmation': {
                        'confirmation_url': result['confirmation']['confirmation_url']
                    }
                }
            else:
                print("❌ В ответе нет URL для оплаты")
                return None
            
        except requests.exceptions.ConnectTimeout:
            print("❌ Таймаут соединения с ЮKassa")
            return None
        except requests.exceptions.ReadTimeout:
            print("❌ Таймаут чтения ответа от ЮKassa")
            return None
        except requests.exceptions.SSLError as e:
            print(f"❌ Ошибка SSL: {e}")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Ошибка соединения: {e}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка при создании платежа: {e}")
            print(f"Тип ошибки: {type(e).__name__}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            print(f"Тип ошибки: {type(e).__name__}")
            return None
    
    def get_payment(self, payment_id):
        """
        Получает информацию о платеже
        
        Args:
            payment_id (str): ID платежа в ЮKassa
        
        Returns:
            dict: Информация о платеже
        """
        url = f"{self.base_url}/payments/{payment_id}"
        
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при получении информации о платеже: {e}")
            return None
    
    def capture_payment(self, payment_id, amount=None):
        """
        Подтверждает платеж
        
        Args:
            payment_id (str): ID платежа в ЮKassa
            amount (Decimal): Сумма к подтверждению (если None, то полная сумма)
        
        Returns:
            dict: Ответ от API ЮKassa
        """
        url = f"{self.base_url}/payments/{payment_id}/capture"
        
        capture_data = {}
        if amount is not None:
            capture_data["amount"] = {
                "value": str(amount),
                "currency": "RUB"
            }
        
        headers = {
            "Idempotence-Key": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=headers,
                json=capture_data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при подтверждении платежа: {e}")
            return None
    
    def cancel_payment(self, payment_id):
        """
        Отменяет платеж
        
        Args:
            payment_id (str): ID платежа в ЮKassa
        
        Returns:
            dict: Ответ от API ЮKassa
        """
        url = f"{self.base_url}/payments/{payment_id}/cancel"
        
        headers = {
            "Idempotence-Key": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers=headers,
                json={}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отмене платежа: {e}")
            return None


# Создаем глобальный экземпляр клиента
client = YooKassaClient()


def create_payment(amount, description, return_url=None, metadata=None):
    """
    Функция-обертка для создания платежа через глобальный экземпляр клиента
    """
    return client.create_payment(amount, description, return_url, metadata)


def process_webhook(webhook_data):
    """
    Обработка уведомлений от ЮKassa
    
    Args:
        webhook_data (dict): Данные уведомления
    
    Returns:
        bool: True если уведомление успешно обработано
    """
    try:
        event_type = webhook_data.get('event')
        payment_data = webhook_data.get('object')
        
        if event_type == 'payment.succeeded':
            # Платеж успешно завершен
            payment_id = payment_data.get('id')
            
            # Здесь нужно обновить статус платежа в базе данных
            from .models import Payment, PaymentHistory
            
            try:
                payment = Payment.objects.get(yookassa_payment_id=payment_id)
                payment.status = 'succeeded'
                payment.payment_method = payment_data.get('payment_method', {})
                payment.save()
                
                # Создаем запись в истории оплат
                PaymentHistory.objects.create(
                    user=payment.user,
                    payment=payment,
                    month=payment.payment_month,
                    year=payment.payment_year,
                    amount_paid=payment.amount,
                    pricing_plan=payment.pricing_plan
                )
                
                return True
            except Payment.DoesNotExist:
                print(f"Платеж {payment_id} не найден в базе данных")
                return False
        
        elif event_type == 'payment.canceled':
            # Платеж отменен
            payment_id = payment_data.get('id')
            
            try:
                payment = Payment.objects.get(yookassa_payment_id=payment_id)
                payment.status = 'canceled'
                payment.save()
                return True
            except Payment.DoesNotExist:
                print(f"Платеж {payment_id} не найден в базе данных")
                return False
        
        return True
    except Exception as e:
        print(f"Ошибка при обработке webhook: {e}")
        return False