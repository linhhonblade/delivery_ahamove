Ahamove Integration for Odoo

# TODO

## Functionality

- [ ] Prodcution and Staging url
  
Handle Exception:

- [ ] Exceptions which raise UserWarning
- [ ] Exceptions which raise UserError

## Testing

- [ ] Create order and get rate shipment
- [ ] Confirm order and validate the delivery
- [ ] Get tracking url
- [ ] Cancel shipment

### Case 1: Simulate the whole process from creating sale order to cancel shipment
- Create a sale order:
    - product: storable type with some qty on hand
    - customer: in Vietnam
    - company address: in Vietnam
- Get rate shipment and add to the sale order
- Confirm sale order
    - Check the picking
- Set qty done on stock moves
- Validate the picking
    - Check if the tracking number is generated
    - Check the tracking url is generated
- Cancel the shipping
    - Check the tracking number and tracking url is set to False

### Case 2: Simulate the process in case user choose wrong service type
### Case 3: Simulate the process in case the address not found

## Prepare demo data

- [ ] Company and Customer in Vietnam
- [ ] currency VND
- [ ] A sample service type