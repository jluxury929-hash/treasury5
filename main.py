# TREASURY v7.0 - REAL MAINNET ETH EARNING
# Makes ACTUAL blockchain transactions to claim ETH from contracts

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from eth_account import Account
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Treasury v7.0 - REAL MAINNET ETH")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Smart contracts on MAINNET that hold REAL ETH
EARNING_CONTRACTS = [
    "0x29983BE497D4c1D39Aa80D20Cf74173ae81D2af5",
    "0x0b8Add0d32eFaF79E6DB4C58CcA61D6eFBCcAa3D",
    "0xf97A395850304b8ec9B8f9c80A17674886612065"
]

# Standard withdrawal contract ABI
WITHDRAWAL_ABI = [
    {"inputs": [{"name": "amount", "type": "uint256"}], "name": "withdraw", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "claim", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "withdrawTo", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "getBalance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

ALCHEMY_URL = os.getenv("ALCHEMY_URL", "https://eth-mainnet.g.alchemy.com/v2/j6uyDNnArwlEpG44o93SqZ0JixvE20Tq")
TREASURY_PRIVATE_KEY = os.getenv("TREASURY_PRIVATE_KEY", "0xabb69dff9516c0a2c53d4fc849a3fbbac280ab7f52490fd29a168b5e3292c45f
")

w3 = None
treasury_account = None
total_real_eth_earned = 0.0

try:
    logger.info("🔥 Initializing REAL MAINNET ETH EARNING ENGINE...")
    
    if not ALCHEMY_URL or not TREASURY_PRIVATE_KEY:
        raise Exception("Missing ALCHEMY_URL or TREASURY_PRIVATE_KEY")
    
    clean_key = TREASURY_PRIVATE_KEY.strip()
    if not clean_key.startswith("0x"):
        clean_key = "0x" + clean_key
    
    if len(clean_key) != 66:
        raise Exception(f"Invalid key length: {len(clean_key)}")
    
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    
    if not w3.is_connected():
        raise Exception("Web3 not connected to MAINNET")
    
    # Verify we're on MAINNET
    chain_id = w3.eth.chain_id
    if chain_id != 1:
        logger.warning(f"⚠️ NOT ON MAINNET! Chain ID: {chain_id}")
    else:
        logger.info("✅ CONNECTED TO ETHEREUM MAINNET")
    
    treasury_account = Account.from_key(clean_key)
    balance = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
    
    logger.info(f"💰 Treasury: {treasury_account.address}")
    logger.info(f"💰 Balance: {balance} ETH")
    
    # Check contracts on mainnet
    for contract in EARNING_CONTRACTS:
        code = w3.eth.get_code(contract)
        contract_bal = float(w3.from_wei(w3.eth.get_balance(contract), 'ether'))
        logger.info(f"📜 {contract}: {contract_bal} ETH {'✅' if len(code) > 2 else '❌'}")
    
    logger.info("🔥 READY TO CLAIM REAL MAINNET ETH")
    
except Exception as e:
    logger.error(f"❌ Init failed: {str(e)}")

class EarningEvent(BaseModel):
    amountUSD: float
    source: str = "site_activity"
    userId: str = None
    activityType: str = "mining"

class WithdrawalRequest(BaseModel):
    userWallet: str
    amountETH: float
    amountUSD: float = None
    backupId: str = None
    source: str = "user"

class ContractFundRequest(BaseModel):
    contractAddress: str
    amountETH: float

@app.get("/")
@app.get("/health")
@app.get("/api/health")
@app.get("/status")
async def health():
    try:
        if w3 and w3.is_connected() and treasury_account:
            balance = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
            
            contract_balances = {}
            total_contract_eth = 0.0
            for contract in EARNING_CONTRACTS:
                try:
                    bal = w3.eth.get_balance(contract)
                    eth_bal = float(w3.from_wei(bal, 'ether'))
                    contract_balances[contract] = eth_bal
                    total_contract_eth += eth_bal
                except:
                    contract_balances[contract] = 0
            
            return {
                "status": "online",
                "version": "7.0-REAL-MAINNET-ETH",
                "network": "MAINNET" if w3.eth.chain_id == 1 else f"NOT-MAINNET-{w3.eth.chain_id}",
                "treasury_address": treasury_account.address,
                "treasury_eth_balance": balance,
                "balance": balance,
                "total_real_eth_earned": total_real_eth_earned,
                "contract_eth_balance": total_contract_eth,
                "real_eth_earning_active": True,
                "can_withdraw": balance > 0.001,
                "earning_contracts": EARNING_CONTRACTS,
                "contract_balances": contract_balances,
                "chain_id": w3.eth.chain_id,
                "block_number": w3.eth.block_number,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"status": "error", "message": "Not initialized"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/earn")
@app.post("/api/fund/treasury")
async def earn_real_mainnet_eth(event: EarningEvent):
    """
    REAL MAINNET ETH EARNING ENGINE
    Makes ACTUAL blockchain transactions to claim ETH from contracts
    """
    global total_real_eth_earned
    
    try:
        if not w3 or not treasury_account:
            raise HTTPException(503, "Earning engine not ready")
        
        if w3.eth.chain_id != 1:
            logger.warning(f"⚠️ NOT ON MAINNET! Chain: {w3.eth.chain_id}")
        
        eth_price = 3450
        target_eth = event.amountUSD / eth_price
        
        logger.info("=" * 80)
        logger.info("🔥 REAL MAINNET ETH EARNING EVENT")
        logger.info(f"💰 Site Activity: undefined")
        logger.info(f"💰 Target ETH: {target_eth} ETH")
        logger.info(f"📍 Source: {event.source}")
        logger.info(f"🌐 Network: {'MAINNET' if w3.eth.chain_id == 1 else f'Chain {w3.eth.chain_id}'}")
        logger.info("=" * 80)
        
        balance_before = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
        real_eth_claimed = 0.0
        successful_claims = []
        
        # Try to claim from each contract
        for contract_address in EARNING_CONTRACTS:
            try:
                # Check contract balance
                contract_balance = float(w3.from_wei(w3.eth.get_balance(contract_address), 'ether'))
                
                if contract_balance < 0.0001:
                    logger.info(f"⏭️ {contract_address}: {contract_balance} ETH (too low)")
                    continue
                
                # Calculate claim amount (10% of contract balance or target amount, whichever is smaller)
                claim_amount = min(target_eth / len(EARNING_CONTRACTS), contract_balance * 0.1, 0.01)
                
                if claim_amount < 0.0001:
                    continue
                
                logger.info(f"📥 Claiming {claim_amount} ETH from {contract_address}...")
                
                # Create contract instance
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(contract_address),
                    abi=WITHDRAWAL_ABI
                )
                
                # Try different withdrawal methods
                tx_hash = None
                
                # Method 1: Try withdrawTo(treasury, amount)
                try:
                    claim_wei = w3.to_wei(claim_amount, 'ether')
                    tx = contract.functions.withdrawTo(
                        treasury_account.address,
                        claim_wei
                    ).build_transaction({
                        'from': treasury_account.address,
                        'nonce': w3.eth.get_transaction_count(treasury_account.address),
                        'gas': 100000,
                        'gasPrice': w3.eth.gas_price,
                        'chainId': w3.eth.chain_id
                    })
                    
                    signed_tx = w3.eth.account.sign_transaction(tx, treasury_account.key)
                    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                    logger.info(f"✅ withdrawTo() TX: {tx_hash.hex()}")
                    
                except Exception as e1:
                    logger.info(f"withdrawTo failed: {str(e1)[:100]}")
                    
                    # Method 2: Try withdraw(amount)
                    try:
                        tx = contract.functions.withdraw(claim_wei).build_transaction({
                            'from': treasury_account.address,
                            'nonce': w3.eth.get_transaction_count(treasury_account.address),
                            'gas': 100000,
                            'gasPrice': w3.eth.gas_price,
                            'chainId': w3.eth.chain_id
                        })
                        
                        signed_tx = w3.eth.account.sign_transaction(tx, treasury_account.key)
                        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                        logger.info(f"✅ withdraw() TX: {tx_hash.hex()}")
                        
                    except Exception as e2:
                        logger.info(f"withdraw failed: {str(e2)[:100]}")
                        
                        # Method 3: Try claim()
                        try:
                            tx = contract.functions.claim().build_transaction({
                                'from': treasury_account.address,
                                'nonce': w3.eth.get_transaction_count(treasury_account.address),
                                'gas': 100000,
                                'gasPrice': w3.eth.gas_price,
                                'chainId': w3.eth.chain_id
                            })
                            
                            signed_tx = w3.eth.account.sign_transaction(tx, treasury_account.key)
                            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
                            logger.info(f"✅ claim() TX: {tx_hash.hex()}")
                            
                        except Exception as e3:
                            logger.error(f"❌ All methods failed for {contract_address}")
                            continue
                
                if tx_hash:
                    # Wait for transaction receipt
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                    
                    if receipt['status'] == 1:
                        real_eth_claimed += claim_amount
                        successful_claims.append({
                            'contract': contract_address,
                            'amount': claim_amount,
                            'tx': tx_hash.hex(),
                            'block': receipt['blockNumber']
                        })
                        logger.info(f"✅ CLAIMED {claim_amount} ETH - Block {receipt['blockNumber']}")
                    else:
                        logger.error(f"❌ Transaction failed: {tx_hash.hex()}")
                
            except Exception as e:
                logger.error(f"❌ Contract {contract_address}: {str(e)[:200]}")
                continue
        
        # Check new balance
        balance_after = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
        actual_eth_gained = balance_after - balance_before
        
        total_real_eth_earned += actual_eth_gained
        
        logger.info("=" * 80)
        logger.info(f"🎉 REAL ETH CLAIMED: {actual_eth_gained} ETH")
        logger.info(f"💰 Balance Before: {balance_before} ETH")
        logger.info(f"💰 Balance After: {balance_after} ETH")
        logger.info(f"💰 Total Real ETH Earned: {total_real_eth_earned} ETH")
        logger.info(f"✅ Successful Claims: {len(successful_claims)}")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "real_eth_claimed": actual_eth_gained,
            "target_eth": target_eth,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "total_real_eth_earned": total_real_eth_earned,
            "successful_claims": successful_claims,
            "contracts_attempted": len(EARNING_CONTRACTS),
            "contracts_succeeded": len(successful_claims),
            "network": "MAINNET" if w3.eth.chain_id == 1 else f"Chain-{w3.eth.chain_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Earning failed: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/api/claim/earnings")
@app.post("/withdraw")
@app.post("/api/withdraw")
async def withdraw(req: WithdrawalRequest):
    """Send REAL MAINNET ETH to user wallets"""
    try:
        logger.info("=" * 80)
        logger.info("💸 REAL MAINNET ETH WITHDRAWAL")
        logger.info(f"💰 Amount: {req.amountETH} ETH")
        logger.info(f"📍 To: {req.userWallet}")
        logger.info(f"🌐 Network: {'MAINNET' if w3.eth.chain_id == 1 else f'Chain {w3.eth.chain_id}'}")
        logger.info("=" * 80)
        
        if not w3 or not treasury_account:
            raise HTTPException(503, "Backend not ready")
        
        if not Web3.is_address(req.userWallet):
            raise HTTPException(400, "Invalid address")
        
        if req.amountETH <= 0 or req.amountETH > 10:
            raise HTTPException(400, "Invalid amount")
        
        balance = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
        
        if balance < req.amountETH + 0.001:
            raise HTTPException(400, f"Insufficient: {balance} ETH")
        
        amount_wei = w3.to_wei(req.amountETH, 'ether')
        
        transaction = {
            'nonce': w3.eth.get_transaction_count(treasury_account.address),
            'to': Web3.to_checksum_address(req.userWallet),
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        }
        
        signed_txn = w3.eth.account.sign_transaction(transaction, treasury_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        
        logger.info(f"✅ REAL ETH SENT: {tx_hash_hex}")
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        new_balance = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
        
        logger.info(f"🎉 SUCCESS! New balance: {new_balance} ETH")
        logger.info("=" * 80)
        
        return {
            "success": True,
            "txHash": tx_hash_hex,
            "transactionHash": tx_hash_hex,
            "blockNumber": receipt['blockNumber'],
            "gasUsed": receipt['gasUsed'],
            "amountETH": req.amountETH,
            "recipientWallet": req.userWallet,
            "treasuryAddress": treasury_account.address,
            "oldBalance": balance,
            "newBalance": new_balance,
            "etherscanUrl": f"https://etherscan.io/tx/{tx_hash_hex}",
            "network": "MAINNET" if w3.eth.chain_id == 1 else f"Chain-{w3.eth.chain_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Withdrawal failed: {str(e)}")
        raise HTTPException(500, str(e))

@app.post("/api/fund/contract")
async def fund_contract(req: ContractFundRequest):
    """Send REAL ETH to contracts"""
    logger.info(f"📥 Fund contract {req.contractAddress}: {req.amountETH} ETH")
    
    if not w3 or not treasury_account:
        raise HTTPException(503, "Backend not ready")
    
    if not Web3.is_address(req.contractAddress):
        raise HTTPException(400, "Invalid contract")
    
    try:
        balance = float(w3.from_wei(w3.eth.get_balance(treasury_account.address), 'ether'))
        
        if balance < req.amountETH + 0.001:
            raise HTTPException(400, "Insufficient balance")
        
        amount_wei = w3.to_wei(req.amountETH, 'ether')
        
        transaction = {
            'nonce': w3.eth.get_transaction_count(treasury_account.address),
            'to': Web3.to_checksum_address(req.contractAddress),
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        }
        
        signed_txn = w3.eth.account.sign_transaction(transaction, treasury_account.key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        logger.info(f"✅ Contract funded: {tx_hash_hex}")
        
        return {
            "success": True,
            "txHash": tx_hash_hex,
            "contractAddress": req.contractAddress,
            "amount": req.amountETH,
            "blockNumber": receipt['blockNumber']
        }
    except Exception as e:
        logger.error(f"❌ Contract funding failed: {str(e)}")
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
