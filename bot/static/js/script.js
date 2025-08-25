document.addEventListener('DOMContentLoaded', function() {
            // Фильтрация студентов
            const filterButtons = document.querySelectorAll('.filter-btn');
            const studentCards = document.querySelectorAll('.student-card');
            
            filterButtons.forEach(button => {
                button.addEventListener('click', function() {
                    // Удаляем активный класс у всех кнопок
                    filterButtons.forEach(btn => btn.classList.remove('active'));
                    // Добавляем активный класс текущей кнопке
                    this.classList.add('active');
                    
                    const filter = this.textContent.trim();
                    
                    studentCards.forEach(card => {
                        const statusElement = card.querySelector('.payment-status');
                        
                        if (filter === 'Все ученики') {
                            card.style.display = 'block';
                            setTimeout(() => {
                                card.style.opacity = '1';
                                card.style.transform = 'translateY(0) scale(1)';
                            }, 20);
                        } else if (filter === 'Оплатившие' && statusElement.classList.contains('status-paid')) {
                            card.style.display = 'block';
                            setTimeout(() => {
                                card.style.opacity = '1';
                                card.style.transform = 'translateY(0) scale(1)';
                            }, 20);
                        } else if (filter === 'Ожидающие' && statusElement.classList.contains('status-pending')) {
                            card.style.display = 'block';
                            setTimeout(() => {
                                card.style.opacity = '1';
                                card.style.transform = 'translateY(0) scale(1)';
                            }, 20);
                        } else if (filter === 'Не оплатившие' && statusElement.classList.contains('status-unpaid')) {
                            card.style.display = 'block';
                            setTimeout(() => {
                                card.style.opacity = '1';
                                card.style.transform = 'translateY(0) scale(1)';
                            }, 20);
                        } else {
                            card.style.opacity = '0';
                            card.style.transform = 'translateY(20px) scale(0.95)';
                            setTimeout(() => {
                                card.style.display = 'none';
                            }, 400);
                        }
                    });
                });
            });
            
            // Обработка кнопок действий
            const actionButtons = document.querySelectorAll('.action-btn');
            
            actionButtons.forEach(button => {
                button.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const card = this.closest('.student-card');
                    const studentName = card.querySelector('.student-name').textContent;
                    
                    if (this.textContent.includes('Напомнить')) {
                        this.innerHTML = '<i class="fas fa-check"></i> Отправлено';
                        this.style.background = 'var(--success)';
                        this.style.color = 'white';
                        this.style.borderColor = 'var(--success)';
                        
                        setTimeout(() => {
                            this.innerHTML = '<i class="fas fa-envelope"></i> Напомнить';
                            this.style.background = '';
                            this.style.color = '';
                            this.style.borderColor = '';
                        }, 2000);
                    } else if (this.textContent.includes('Оплата')) {
                        const statusElement = card.querySelector('.payment-status');
                        statusElement.textContent = 'Оплачено';
                        statusElement.className = 'payment-status status-paid';
                        
                        this.innerHTML = '<i class="fas fa-check-double"></i> Готово';
                        this.style.background = 'var(--success)';
                        
                        setTimeout(() => {
                            this.innerHTML = '<i class="fas fa-check"></i> Оплата';
                            this.style.background = '';
                        }, 2000);
                    }
                });
            });
            
            // Автоматическое открытие текущего месяца
            const currentMonth = new Date();
            const currentMonthElement = document.getElementById(`month-${12 - currentMonth.getMonth()}`);
            if (currentMonthElement) {
                currentMonthElement.classList.add('expanded');
                const header = currentMonthElement.previousElementSibling;
                header.querySelector('.collapse-icon').classList.add('rotated');
            }
        });
        
        function toggleMonth(monthId, element) {
            const content = document.getElementById(monthId);
            const icon = element.querySelector('.collapse-icon');
            
            content.classList.toggle('expanded');
            icon.classList.toggle('rotated');
            
            // Плавная прокрутка к развернутому месяцу
            if (content.classList.contains('expanded')) {
                setTimeout(() => {
                    content.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }, 300);
            }
        }