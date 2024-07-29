document.addEventListener('DOMContentLoaded', function() {
    const ruleInputs = document.getElementById('rule-inputs');
    const addMoreBtn = document.getElementById('add-more-btn');
    const submitRuleBtn = document.getElementById('submit-rule-btn');
    const viewRulesBtn = document.getElementById('view-rules-btn');
    const deleteAllBtn = document.getElementById('delete-all-btn');
    const confirmation = document.getElementById('confirmation');
    const confirmYesBtn = document.getElementById('confirm-yes-btn');
    const confirmNoBtn = document.getElementById('confirm-no-btn');
    const rulesList = document.getElementById('rules-list');
    const editDeleteConfirmation = document.getElementById('edit-delete-confirmation');
    const editDeleteMessage = document.getElementById('edit-delete-message');
    const confirmEditDeleteYesBtn = document.getElementById('confirm-edit-delete-yes-btn');
    const confirmEditDeleteNoBtn = document.getElementById('confirm-edit-delete-no-btn');

    let editDeleteAction = null;
    let currentRule = null;
    let rulesVisible = false;

    const urlPrefix = ''; // Update this if needed

    addMoreBtn.addEventListener('click', () => {
        const newInput = document.createElement('div');
        newInput.className = 'rule-input';
        newInput.innerHTML = '<input type="text" placeholder="ID" class="id-input"><input type="text" placeholder="PRICE" class="price-input">';
        ruleInputs.appendChild(newInput);
    });

    submitRuleBtn.addEventListener('click', () => {
        const ids = document.querySelectorAll('.id-input');
        const prices = document.querySelectorAll('.price-input');
        const rules = [];
        ids.forEach((idInput, index) => {
            const id = idInput.value.trim();
            const price = prices[index].value.trim();
            if (id && price) {
                rules.push({ id, price });
            }
        });
        if (rules.length > 0) {
            fetch(`${urlPrefix}/add_rule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rules)
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            }).then(data => {
                if (data.success) {
                    ids.forEach(input => input.value = '');
                    prices.forEach(input => input.value = '');
                    console.log('Правила успешно добавлены');
                    if (rulesVisible) {
                        viewRulesBtn.click();
                    }
                }
            }).catch(error => console.error('Error:', error));
        }
    });

    viewRulesBtn.addEventListener('click', () => {
        if (rulesVisible) {
            rulesList.classList.add('hidden');
            rulesVisible = false;
        } else {
            fetch(`${urlPrefix}/get_rules`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(rules => {
                    rulesList.innerHTML = '';
                    for (const id in rules) {
                        const ruleItem = document.createElement('div');
                        ruleItem.className = 'rule-item';
                        ruleItem.innerHTML = `
                            <input type="text" value="${id}" class="id-input" disabled>
                            <input type="text" value="${rules[id]}" class="price-input">
                            <button class="edit-rule-btn">Edit</button>
                            <button class="delete-rule-btn">Delete</button>
                        `;
                        rulesList.appendChild(ruleItem);

                        ruleItem.querySelector('.delete-rule-btn').addEventListener('click', () => {
                            currentRule = { id, price: rules[id] };
                            editDeleteAction = 'delete';
                            editDeleteMessage.textContent = `Вы уверены что хотите удалить ID: ${id} с PRICE: ${rules[id]}?`;
                            editDeleteConfirmation.classList.remove('hidden');
                            rulesList.appendChild(editDeleteConfirmation);
                        });

                        ruleItem.querySelector('.edit-rule-btn').addEventListener('click', () => {
                            const newPrice = ruleItem.querySelector('.price-input').value.trim();
                            if (newPrice) {
                                currentRule = { id, price: newPrice };
                                editDeleteAction = 'edit';
                                editDeleteMessage.textContent = `Вы уверены что хотите изменить ID: ${id} с PRICE: ${rules[id]} на PRICE ${newPrice}?`;
                                editDeleteConfirmation.classList.remove('hidden');
                                rulesList.appendChild(editDeleteConfirmation);
                            }
                        });
                    }
                    rulesList.classList.remove('hidden');
                    rulesVisible = true;
                })
                .catch(error => console.error('Error:', error));
        }
    });

    deleteAllBtn.addEventListener('click', () => {
        confirmation.classList.remove('hidden');
        viewRulesBtn.classList.add('hidden');
        deleteAllBtn.classList.add('hidden');
        rulesList.classList.add('hidden');
        rulesVisible = false;
    });

    confirmYesBtn.addEventListener('click', () => {
        fetch(`${urlPrefix}/delete_all_rules`, { method: 'POST' })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    rulesList.innerHTML = '';
                    confirmation.classList.add('hidden');
                    viewRulesBtn.classList.remove('hidden');
                    deleteAllBtn.classList.remove('hidden');
                    console.log('Все правила удалены');
                }
            })
            .catch(error => console.error('Error:', error));
    });

    confirmNoBtn.addEventListener('click', () => {
        confirmation.classList.add('hidden');
        viewRulesBtn.classList.remove('hidden');
        deleteAllBtn.classList.remove('hidden');
    });

    confirmEditDeleteYesBtn.addEventListener('click', () => {
        if (editDeleteAction === 'delete') {
            fetch(`${urlPrefix}/delete_rule/${currentRule.id}`, { method: 'POST' })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        editDeleteConfirmation.classList.add('hidden');
                        viewRulesBtn.click();
                        console.log(`Правило с ID: ${currentRule.id} удалено`);
                    }
                })
                .catch(error => console.error('Error:', error));
        } else if (editDeleteAction === 'edit') {
            fetch(`${urlPrefix}/edit_rule`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: currentRule.id, price: currentRule.price })
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            }).then(data => {
                if (data.success) {
                    editDeleteConfirmation.classList.add('hidden');
                    viewRulesBtn.click();
                    console.log(`Правило с ID: ${currentRule.id} обновлено`);
                }
            }).catch(error => console.error('Error:', error));
        }
    });

    confirmEditDeleteNoBtn.addEventListener('click', () => {
        editDeleteConfirmation.classList.add('hidden');
    });

    document.getElementById('new-id').addEventListener('blur', () => {
        const newId = document.getElementById('new-id').value.trim();
        if (newId) {
            fetch(`${urlPrefix}/get_rules`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(rules => {
                    if (rules.hasOwnProperty(newId)) {
                        const newPrice = document.getElementById('new-price').value.trim();
                        currentRule = { id: newId, price: newPrice };
                        editDeleteAction = 'edit';
                        editDeleteMessage.textContent = `Запись с таким ID уже есть! Хотите перезаписать его с ID: ${newId} с PRICE: ${rules[newId]} на PRICE ${newPrice}?`;
                        editDeleteConfirmation.classList.remove('hidden');
                        rulesList.appendChild(editDeleteConfirmation);
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    });
});
