SELECT
    m.membership_id,
    m.first_name,
    m.last_name,
    SUM(st.total_items_price) AS total_spending
FROM members AS m
JOIN sales_transactions AS st
    ON m.membership_id = st.membership_id
GROUP BY
    m.membership_id,
    m.first_name,
    m.last_name
ORDER BY total_spending DESC
LIMIT 10;

SELECT
    i.item_name,
    SUM(ti.quantity) AS total_quantity
FROM items AS i
JOIN transaction_items AS ti
    ON i.item_id = ti.item_id
GROUP BY
    i.item_id,
    i.item_name
ORDER BY total_quantity DESC
LIMIT 3;