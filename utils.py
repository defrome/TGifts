PAYMENT_SUCCESS = (
    "🎉 <b>Payment successful!</b>\n"
    "💲 <b>Amount:</b> {amount}⭐️\n"
    "🆔 <b>Transaction ID:</b> <code>{transaction_id}</code>"
)

PAYMENT_ERROR = "❌ <b>Failed to create payment invoice</b>"
REFUND_SUCCESS = "✅ <b>Payment has been successfully refunded!</b>"
REFUND_FAIL = "❌ <b>Failed to refund payment</b>"
INVALID_COMMAND = ("❌ <b>Please use format:</b> /refund '&lt;transaction_id&gt;'\n"
                   "Example: <code>/refund ABC123XYZ</code>")