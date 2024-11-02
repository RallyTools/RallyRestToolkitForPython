#!/usr/bin/env python
###################################################################################################
#
# vsm_ops_explore - Make a couple of Products, a few Components
#                   and then see if you can a couple of Components to a Product
#                   via the Children Collection on the Product
#
#    We've proved that pyral via rally.update can add multiple Components to a Product
#    and that we can add Products to a Component in the same manner.
#
#    We also prove in here that we can add a single Component to a Product
#    that already has multiple Components in its Collection
#
###################################################################################################

PRODUCT_1 = 'Gombo'
PRODUCT_2 = 'Vokyndol'

COMPONENT_1 = 'Libenni'
COMPONENT_2 = 'Feradoj'
COMPONENT_3 = 'Jinklen'
COMPONENT_4 = 'Narviktus'
COMPONENT_5 = 'Sarbinoz'
COMPONENT_6 = 'Zikmosqi'

CONF = 'yeti.cfg'
WORKSPACE = 'Yeti Rally Workspace'
PROJECT   = 'Little Claus'

###################################################################################################

import sys, os
from pyral import Rally, rallyWorkset, RallyRESTAPIError

###################################################################################################
###################################################################################################

def main(args):
    args = []
    options = [f'--conf={CONF}', f'--rallyWorkspace={WORKSPACE}', f'--rallyProject={PROJECT}']
    server, user, password, api_key, workspace, project = rallyWorkset(options)

    rally = Rally(server, user, apikey=api_key, workspace=workspace, project=project)

    response = rally.get('VSMProduct')
    print(response.status_code)
    num_vsm_products = response.resultCount
    print(f'There are {num_vsm_products} VSMProduct records')
    if num_vsm_products:
        products = [item for item in response]
    else:
        products = addSomeNewVSMProducts(rally)

    response = rally.get('VSMComponent')
    print(response.status_code)
    num_vsm_components = response.resultCount
    print(f'There are {num_vsm_components} VSMComponent records')
    if num_vsm_components:
        components = [item for item in response]
    else:
        components = addSomeNewVSMComponents(rally)

    prod_1_components = [COMPONENT_1, COMPONENT_2, COMPONENT_5]
    prod_2_components = [COMPONENT_1, COMPONENT_3, COMPONENT_4, COMPONENT_6]

    # Get Components associated to Product_1 via the components Products Collection
    # Get Components associated to Product_2 via the products   Components Collection
    prod_1, prod_2 = products[:2]

    comp_1 = components[0]
    comp_2 = components[1]
    comp_3 = components[2]
    comp_4 = components[3]
    comp_5 = components[4]
    comp_6 = components[5]

    result = rally.addCollectionItems(prod_1, 'Components', [comp_3])
    print(f'Product: {result.oid}  {result.Name}')
    for comp in result.Components:
        print(f'    {comp.oid} {comp.Name}')

    print(result)

    #showProductComponents(rally, prod_1.Name)

    prod_1 = setProductComponents(rally, prod_1, [comp_1, comp_2, comp_5])
    print(f'Product_1 ({prod_1.Name}) Components')
    for comp in prod_1.Components:
        print(f'    {comp.oid} {comp.Name}')

    setComponentProducts(rally, comp_1, [prod_1, prod_2])
    setComponentProducts(rally, comp_2, [prod_1])
    setComponentProducts(rally, comp_3, [prod_2])
    setComponentProducts(rally, comp_4, [prod_1, prod_2])
    setComponentProducts(rally, comp_5, [prod_1])
    setComponentProducts(rally, comp_6, [prod_2])

    response = rally.get('VSMProduct', fetch="ObjectID,Name,Components", query=f'Name = "{PRODUCT_1}"')
    if response.resultCount == 1:
        prod_1 = response.next()
    print(f"Product number 1: {prod_1.Name}")
    components = [f'{comp.oid} {comp.Name}' for comp in prod_1.Components]
    print(f"   Components: {components}")

    response = rally.get('VSMComponent', fetch="ObjectID,Name,Products", query=f'Name = "{COMPONENT_4}"')
    if response.resultCount == 1:
        comp_4 = response.next()
    print(f"Component number 4: {comp_4.Name}")
    products = [f'{prod.oid} {prod.Name}' for prod in comp_4.Products]
    print(f"   Products: {products}")

    print('DONE')

###################################################################################################

def showProductComponents(rally, product_name):
    response = rally.get('VSMProduct', fetch="ObjectID,Name,Components", query=f'Name = "{product_name}"')
    if response.resultCount == 1:
        prod = response.next()
        print(f'Product ({prod.Name}) Components')
        for comp in prod.Components:
            print(f'    {comp.oid} {comp.Name}')
    return True

###################################################################################################

def addProduct(rally, product_name):
    item = None
    fodder = {'Name' : product_name}   # 'SubclassType' : 'Foonizork'
    item = rally.create('VSMProduct', fodder)
    return item

###################################################################################################

def addComponent(rally, component_name, product=None):
    item = None
    fodder = {'Name': component_name}
    item = rally.create('VSMComponent', fodder)

    if product:
        data = {'Products': [product.oid]}
        item = rally.update('VSMComponent', item.oid, {data})
    return item

###################################################################################################

def addSomeNewVSMProducts(rally):
    prod_1 = addProduct(rally, PRODUCT_1)
    prod_2 = addProduct(rally, PRODUCT_2)

def addSomeNewVSMComponents(rally):
    comp_1 = addComponent(rally, COMPONENT_1)
    comp_2 = addComponent(rally, COMPONENT_2)
    comp_3 = addComponent(rally, COMPONENT_3)
    comp_4 = addComponent(rally, COMPONENT_4)
    comp_5 = addComponent(rally, COMPONENT_5)
    comp_6 = addComponent(rally, COMPONENT_6)

###################################################################################################

def setProductComponents(rally, product, components):
    upd = {'ObjectID'   : product.oid,
           'Components' : components
          }
    updated_product = rally.update('VSMProduct', upd)
    return updated_product

def setComponentProducts(rally, component, products):
    upd = {'ObjectID' : component.oid,
           'Products' : products
          }
    updated_component = rally.update('VSMComponent', upd)
    return updated_component

###################################################################################################
###################################################################################################

if __name__ == "__main__":
    main(sys.argv[1:])
