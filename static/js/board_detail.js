let draggedCard = null;
let draggedList = null;

function getBoardId() {
    const container = document.getElementById('lists-container');
    return container ? parseInt(container.dataset.boardId) : null;
}

window.goToBoards = function() {
    sendData({action: "boards->send_page", data: {}});
};

window.showEditBoardNameModal = function() {
    const boardId = getBoardId();
    const boardName = document.querySelector('.board-header h2')?.textContent || '';
    const modal = document.getElementById('modal-container');
    if (modal) {
        modal.innerHTML = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal" onclick="event.stopPropagation()">
                    <h3>ボード名を編集</h3>
                    <input type="text" id="board-name" value="${boardName}" autofocus>
                    <div class="btn-group">
                        <button class="btn-secondary" onclick="closeModal()">キャンセル</button>
                        <button class="btn-primary" onclick="updateBoardName()">保存</button>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('board-name').focus();
        document.getElementById('board-name').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') updateBoardName();
        });
    }
};

window.updateBoardName = function() {
    const boardId = getBoardId();
    const name = document.getElementById('board-name')?.value.trim();
    if (name && boardId) {
        sendData({action: "board_detail->update_board_name", data: {board_id: boardId, name: name}});
        closeModal();
    }
};

window.closeModal = function() {
    const modal = document.getElementById('modal-container');
    if (modal) {
        modal.innerHTML = '';
    }
};

window.showAddListForm = function() {
    const form = document.getElementById('add-list-form');
    if (form) {
        form.classList.remove('hidden');
        document.getElementById('new-list-name')?.focus();
    }
};

window.hideAddListForm = function() {
    const form = document.getElementById('add-list-form');
    if (form) {
        form.classList.add('hidden');
        const input = document.getElementById('new-list-name');
        if (input) input.value = '';
    }
};

window.addList = function() {
    const boardId = getBoardId();
    const name = document.getElementById('new-list-name')?.value.trim();
    if (name && boardId) {
        sendData({action: "board_detail->add_list", data: {board_id: boardId, name: name}});
        hideAddListForm();
    }
};

window.showEditListModal = function(listId, currentName) {
    const modal = document.getElementById('modal-container');
    if (modal) {
        modal.innerHTML = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal" onclick="event.stopPropagation()">
                    <h3>リストを編集</h3>
                    <input type="text" id="list-name" value="${currentName}" autofocus>
                    <div class="btn-group">
                        <button class="btn-secondary" onclick="closeModal()">キャンセル</button>
                        <button class="btn-primary" onclick="updateList(${listId})">保存</button>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('list-name').focus();
        document.getElementById('list-name').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') updateList(listId);
        });
    }
};

window.updateList = function(listId) {
    const boardId = getBoardId();
    const name = document.getElementById('list-name')?.value.trim();
    if (name && boardId) {
        sendData({action: "board_detail->edit_list", data: {board_id: boardId, list_id: listId, name: name}});
        closeModal();
    }
};

window.deleteList = function(listId) {
    const boardId = getBoardId();
    if (confirm('このリストを削除しますか？') && boardId) {
        sendData({action: "board_detail->remove_list", data: {board_id: boardId, list_id: listId}});
    }
};

window.showAddCardForm = function(listId) {
    const form = document.getElementById('add-card-form-' + listId);
    if (form) {
        form.classList.remove('hidden');
        document.getElementById('new-card-title-' + listId)?.focus();
    }
};

window.hideAddCardForm = function(listId) {
    const form = document.getElementById('add-card-form-' + listId);
    if (form) {
        form.classList.add('hidden');
        const input = document.getElementById('new-card-title-' + listId);
        if (input) input.value = '';
    }
};

window.addCard = function(listId) {
    const boardId = getBoardId();
    const title = document.getElementById('new-card-title-' + listId)?.value.trim();
    if (title && boardId) {
        sendData({action: "board_detail->add_card", data: {board_id: boardId, list_id: listId, title: title}});
        hideAddCardForm(listId);
    }
};

window.showEditCardModal = function(cardId, currentTitle) {
    const modal = document.getElementById('modal-container');
    if (modal) {
        modal.innerHTML = `
            <div class="modal-overlay" onclick="closeModal()">
                <div class="modal" onclick="event.stopPropagation()">
                    <h3>カードを編集</h3>
                    <input type="text" id="card-title" value="${currentTitle}" autofocus>
                    <div class="btn-group">
                        <button class="btn-secondary" onclick="closeModal()">キャンセル</button>
                        <button class="btn-primary" onclick="updateCard(${cardId})">保存</button>
                    </div>
                </div>
            </div>
        `;
        document.getElementById('card-title').focus();
        document.getElementById('card-title').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') updateCard(cardId);
        });
    }
};

window.updateCard = function(cardId) {
    const boardId = getBoardId();
    const title = document.getElementById('card-title')?.value.trim();
    if (title && boardId) {
        sendData({action: "board_detail->edit_card", data: {board_id: boardId, card_id: cardId, title: title}});
        closeModal();
    }
};

window.deleteCard = function(cardId) {
    const boardId = getBoardId();
    if (confirm('このカードを削除しますか？') && boardId) {
        sendData({action: "board_detail->remove_card", data: {board_id: boardId, card_id: cardId}});
    }
};

window.handleCardDragStart = function(event) {
    draggedCard = event.target;
    event.target.classList.add('dragging');
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', event.target.dataset.cardId);
};

window.handleCardDragEnd = function(event) {
    event.target.classList.remove('dragging');
    draggedCard = null;
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
};

window.handleCardDragOver = function(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    const container = event.target.closest('.cards-container');
    if (container) {
        container.classList.add('drag-over');
    }
};

window.handleCardDrop = function(event) {
    event.preventDefault();
    const container = event.target.closest('.cards-container');
    if (container && draggedCard) {
        const boardId = getBoardId();
        const targetListId = container.dataset.listId;
        const cards = Array.from(container.querySelectorAll('.card:not(.dragging)'));
        let targetPosition = cards.length;

        const afterElement = getDragAfterElement(container, event.clientY);
        if (afterElement) {
            targetPosition = parseInt(afterElement.dataset.position);
        }

        sendData({
            action: "board_detail->reorder_card",
            data: {
                board_id: boardId,
                card_id: parseInt(draggedCard.dataset.cardId),
                target_list_id: parseInt(targetListId),
                target_position: targetPosition
            }
        });
    }
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
};

window.handleListDragStart = function(event) {
    if (event.target.classList.contains('list')) {
        draggedList = event.target;
        event.target.classList.add('dragging');
        event.dataTransfer.effectAllowed = 'move';
        event.dataTransfer.setData('text/plain', event.target.dataset.listId);
    }
};

window.handleListDragEnd = function(event) {
    event.target.classList.remove('dragging');
    draggedList = null;
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
};

window.handleListDragOver = function(event) {
    event.preventDefault();
    if (draggedList) {
        event.dataTransfer.dropEffect = 'move';
    }
};

window.handleListDrop = function(event) {
    event.preventDefault();
    if (draggedList && event.target.closest('.list')) {
        const boardId = getBoardId();
        const targetList = event.target.closest('.list');
        if (targetList !== draggedList) {
            const targetPosition = parseInt(targetList.dataset.position);
            sendData({
                action: "board_detail->reorder_list",
                data: {
                    board_id: boardId,
                    list_id: parseInt(draggedList.dataset.listId),
                    target_position: targetPosition
                }
            });
        }
    }
    document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'));
};

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.card:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}
