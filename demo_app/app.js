const members = {
  "10021": {
    memberName: "Ava Nguyen",
    accountNumber: "CHK-10021",
    status: "Active",
    balance: "$12,840.87"
  },
  "10499": {
    memberName: "Marcus Hill",
    accountNumber: "SAV-10499",
    status: "Active",
    balance: "$9,100.10"
  },
  "20241": {
    memberName: "Priya Patel",
    accountNumber: "CHK-20241",
    status: "Closed",
    balance: "$0.00"
  }
};

const resultBox = document.getElementById("member-result");
const input = document.getElementById("member-id");
const searchButton = document.getElementById("search-button");

function renderMember(memberId) {
  const member = members[memberId];
  if (!member) {
    resultBox.innerHTML = '<div class="empty">No such member found for that ID.</div>';
    return;
  }

  const statusClass = member.status === "Active" ? "status-active" : "status-closed";
  resultBox.innerHTML = `
    <div id="member-name">${member.memberName}</div>
    <div class="meta">
      <div class="meta-item">
        <div class="label">Member ID</div>
        <div class="value" id="member-id-value">${memberId}</div>
      </div>
      <div class="meta-item">
        <div class="label">Account Number</div>
        <div class="value" id="account-number">${member.accountNumber}</div>
      </div>
      <div class="meta-item">
        <div class="label">Status</div>
        <div class="value"><span class="${statusClass}" id="account-status">${member.status}</span></div>
      </div>
      <div class="meta-item">
        <div class="label">Available Balance</div>
        <div class="value" id="account-balance">${member.balance}</div>
      </div>
    </div>
  `;
}

searchButton.addEventListener("click", () => {
  const memberId = input.value.trim();
  renderMember(memberId);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    const memberId = input.value.trim();
    renderMember(memberId);
  }
});
