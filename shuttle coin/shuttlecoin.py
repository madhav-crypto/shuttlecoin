# -*- coding: utf-8 -*-
"""
Created on Sun Jan  2 01:01:16 2022

@author: Madhav
"""

#importing the required libraries
import datetime
import hashlib
from flask import Flask ,jsonify , request
import json
import requests
from uuid import uuid4
from urllib.parse import urlparse

class Blockchain():
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof=1,previous_hash='0')
        self.nodes = set()
        
        
    def create_block(self,proof,previous_hash):
        """
        create_block method takes in proof and previous proof to later append
        the particular block into the chain , also the time and the index of the chain 
        is appended
        """
        block = {'index': len(self.chain)+1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof':proof,
                 'previous_hash':previous_hash,
                 'transactions': self.transactions}
        
        self.transactions = []
        self.chain.append(block)
        return block

    
    def hash(self,block):
        """
        hash method returns the hash code for a particular block
        """
        encoded_block = json.dumps(block,sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def get_previous_block(self):
        """
        get_previous_block methods returns the previous block
        """
        return self.chain[-1]
    
    def proof_of_work(self,previous_proof):
        """
        proof of work method take the previous proof and returns the new proof
        which solves the cryptographic puzzle in this case is getting a nonce which 
        has its hash codes starting fours digits as 0
        """
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_op = hashlib.sha256(str(new_proof **2 - previous_proof**2).encode()).hexdigest()
            if hash_op[:4] == '0000':
                check_proof = True
                
            else:
                new_proof += 1
                
        return new_proof
    
    def is_chain_valid(self,chain):
        """
        is_chain_valid checks the chain if its still valid , first checks is the previous hash
        and the hash of the previous block matches , then checks if the proof of work is right
        """
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            proof = block['proof']
            previous_proof = previous_block['proof']
            hashcode = hashlib.sha256(str(proof **2 - previous_proof**2).encode()).hexdigest()
            if hashcode[:4] != '0000':
                return False
            
            else:
                previous_block = block
                block_index += 1
        return True
    
    def add_transactions(self,sender,reciever,amount):
        """
        add_transactions to add transaction details into the block and returns the
        block index
        """
        self.transactions.append({
                'sender': sender,
                'reciever': reciever,
                'amount': amount})
            
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self,address):
        """
        add_node adds the address of all the nodes into the set of nodes
        """
        url_parsed = urlparse(address)
        self.nodes.add(url_parsed.netloc)
        
        
    def update_chain(self):
        """
        update_chain checks for the longest chain out of all the nodes , and updates the chain
        to the longest one available also checks if the chain is valid 
        """
        network = self.nodes
        longest_chain = None
        max_length = len(longest_chain)
        for node in network:
            response = requests.get(f"https://{node}/get_chain")
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
                    
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
    
app = Flask(__name__)

node_address = str(uuid4()).replace('-', '')
# Creating a Blockchain
blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(node_address,'Madhav',1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'transcations': block['transactions'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'the chain is still valid.'}
    else:
        response = {'message': 'something looks kinda sus bro, go check the chain.'}
    return jsonify(response), 200

#adding transactions to the blockchain
@app.route('/add_transactions', methods = ['POST'])
def add_transactions():
    json = request.get_json()
    transaction_keys = ['sender','reciever','amount']
    if not all (key in json for key in transaction_keys):
        return "some of the required details of transactions are missing",400
    
    index = blockchain.add_transactions(json['sender'],json['reciever'],json['amount'])
    response = {'message': f"the transactions has been added to block {index}"}
    return jsonify(response),201

#connecting the nodes of the blockchain
@app.route('/connect_node',methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': f'All the nodes are now connected. The Shuttlecoin blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

#replacing the chain
@app.route('/update_chain',methods=['GET'])
def update_chain():
    chain_replaced = blockchain.update_chain()
    if chain_replaced:
        response = {'message':'The chain has been replaced to the longest one',
                    'new chain':blockchain.chain}
    else:
        response = {'message': 'The chain is still the longest one',
                    'current chain': blockchain.chain}
        
    return jsonify(response),200

# Running the app
app.run(host = '0.0.0.0', port = 5001)
















