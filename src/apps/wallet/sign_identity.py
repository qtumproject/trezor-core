from trezor import ui
from trezor.utils import unimport

@unimport
async def layout_sign_identity(session_id, msg):
    from trezor.messages.SignedIdentity import SignedIdentity
    from trezor.crypto.curve import secp256k1
    from trezor.crypto.hashlib import sha256
    from ustruct import pack, unpack
    from ..common import coins
    from ..common import seed
    from ..common.signverify import message_digest

    identity = ''
    if msg.identity.proto:
        identity += msg.identity.proto + '://'
    if msg.identity.user:
        identity += msg.identity.user + '@'
    if msg.identity.host:
        identity += msg.identity.host
    if msg.identity.port:
        identity += ':' + msg.identity.port
    if msg.identity.path:
        identity += msg.identity.path

    index = msg.identity.index or 0
    identity_hash = sha256(pack('<I', index) + identity).digest()

    address_n = (13, ) + unpack('<IIII', identity_hash[:16])
    address_n = [0x80000000 | x for x in address_n]

    # TODO: proper handling of non-secp256k1 curves
    #       this would need the change of common.seed.get_node function

    ui.display.clear()
    ui.display.text(10, 30, 'Identity:',
                    ui.BOLD, ui.LIGHT_GREEN, ui.BLACK)
    ui.display.text(10, 60, msg.challenge_visual, ui.MONO, ui.WHITE, ui.BLACK)
    ui.display.text(10, 80, identity, ui.MONO, ui.WHITE, ui.BLACK)

    node = await seed.get_node(session_id, address_n)

    coin = coins.by_name('Bitcoin')
    address = node.address(coin.address_type) # hardcoded Bitcoin address type
    pubkey = node.public_key()
    seckey = node.private_key()
    challenge = sha256(msg.challenge_hidden).digest() + sha256(msg.challenge_visual).digest()
    digest = message_digest(coin, challenge)

    signature = secp256k1.sign(seckey, digest)

    return SignedIdentity(address=address, public_key=pubkey, signature=signature)