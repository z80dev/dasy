from vyper.compiler.settings import Settings, anchor_settings
import dasy
from boa.vyper.contract import VyperContract
import boa




# def test_merkle():
#     leaf3 = 0xdca3326ad7e8121bf9cf9c12333e6b2271abe823ec9edfe42f813b1e768fa57b
#     leaf_bytes = leaf3.to_bytes(32, 'big')
#     merkle_root = 0xcc086fcc038189b4641db2cc4f1de3bb132aefbd65d510d817591550937818c7
#     root_bytes = merkle_root.to_bytes(32, 'big')
#     proof = [0x8da9e1c820f9dbd1589fd6585872bc1063588625729e7ab0797cfc63a00bd950, 0x995788ffc103b987ad50f5e5707fd094419eb12d9552cc423bd0cd86a3861433]
#     proof_bytes = [x.to_bytes(32, 'big') for x in proof]
#     vyper_merkle = boa.load("examples/merkle.vy")

#     in1 = 0x835ba2995566015bd49e561c1210937952c6843e10010f333a65b51f69247b44
#     in1 = in1.to_bytes(32, 'big')

#     in2 = 0x97bcb6ec8d1a742a9e39be8bf20cd581d3af6b4faa63e4e72d67ff57a81b72e9
#     in2 = in2.to_bytes(32, 'big')

#     in3 = 0xdd1b8d11e7734e8c06816161afb24a5dfa82761dd92afaec2f037f0cd0e369f4
#     in3 = in3.to_bytes(32, 'big')

#     leaf = 0x1aD91ee08f21bE3dE0BA2ba6918E714dA6B45836000000000000000000000000
#     leaf = leaf.to_bytes(32, 'big')

#     assert vyper_merkle.verify([in1, in2], in3, leaf)


def compile_src(src: str, *args) -> VyperContract:
    ast = dasy.compile(src, include_abi=True)
    return VyperContract(ast, *args)


def compile(filename: str, *args) -> VyperContract:
    with open(filename) as f:
        src = f.read()
        return compile_src(src, *args)


def test_binops():
    src = """
        (defn plus [] :uint256 :external
        (+ 1 2))
    """
    c = compile_src(src)
    assert c.plus() == 3


def test_chain_binops():
    src = """
        (defn plus [] :uint256 :external
        (+ 1 2 3 4 5 6))
    """
    c = compile_src(src)
    assert c.plus() == 21


def test_defvars():
    src = """
    (defvars x :uint256)
    (defn setX [:uint256 x] :external
      (set self/x x))
    (defn getX [] :uint256 [:external :view] self/x)
    """
    c = compile_src(src)
    c.setX(10)
    assert c.getX() == 10


def test_hello_world():
    c = compile("examples/hello_world.dasy")
    assert c.greet() == "Hello World"


def test_include():
    c = compile("examples/mutable_hello.dasy")
    assert c.greet() == "Hello World"
    c.setGreeting("yo yo")
    assert c.greet() == "yo yo"


def test_call_internal():
    c = compile_src(
        """
    (defn _getX [] :uint256 :internal 4)
    (defn useX [] :uint256 :external
      (+ 2 (self/_getX)))
    """
    )
    assert c.useX() == 6


def test_pure_fn():
    c = compile_src(
        """
    (defn pureX [:uint256 x] :uint256 [:external :pure] x)
    """
    )
    assert c.pureX(6) == 6


def test_constructor():
    c = compile("examples/constructor.dasy", "z80", 100)

    createdAt = c.createdAt()
    expiresAt = c.expiresAt()
    assert expiresAt == createdAt + 100
    assert c.name() == "z80"


def test_if():
    c = compile_src(
        """
    (defn absValue [:uint256 x y] :uint256 [:external :pure]
      (if (>= x y)
         (return (- x y))
         (return (- y x))))"""
    )
    assert c.absValue(4, 7) == 3


def test_if_expr():
    c = compile_src(
        """
    (defn absValue [:uint256 x y] :uint256 [:external :pure]
      (if (>= x y)
          (- x y)
          (- y x)))"""
    )
    assert c.absValue(4, 7) == 3


def test_struct():
    c = compile_src(
        """
    (defstruct Person
        age :uint256
        name (string 100))
    (defvars person (public Person))
    (defn __init__ [] :external
      (set (. self/person age) 12))
    (defn memoryPerson [] Person :external
      (def mPers Person self/person)
      (set-in mPers age 10)
      mPers)
    (defn literalPerson [] Person :external
      (Person {:age 100 :name "Foo"}))
    """
    )
    assert c.person()[0] == 12
    assert c.memoryPerson() == (10, "")
    assert c.literalPerson() == (100, "Foo")


def test_arrays():
    c = compile_src(
        """
    (defvars nums (public (array :uint256 10)))
    (defn __init__ [] :external
      (doto self/nums
        (set-at 0 5)
        (set-at 1 10))
      )
    """
    )
    assert c.nums(0) == 5
    assert c.nums(1) == 10


def test_map():
    c = compile_src(
        """
    (defvars myMap (public (hash-map :address :uint256))
            owner (public :address))
    (defn __init__ [] :external
      (set self/owner msg/sender)
      (set-at! self/myMap [msg/sender] 10))
    (defn getOwnerNum [] :uint256 :external
     (get-at! self/myMap [msg/sender]))
    """
    )
    assert c.myMap("0x8B4de256180CFEC54c436A470AF50F9EE2813dbB") == 0
    assert c.myMap(c.owner()) == 10
    assert c.getOwnerNum() == 10


def test_reference_types():
    settings = Settings(evm_version="cancun")
    with anchor_settings(settings):
        c = compile_src(
            """
        (defvar nums (array :uint256 10))
        (defn memoryArrayVal [] '(:uint256 :uint256) :external
        (defvar arr (array :uint256 10) self/nums)
        (set-at arr 1 12)
        '((get-at arr 0) (get-at arr 1)))
        """
        )
        assert c.memoryArrayVal() == (0, 12)

        d = compile("examples/reference_types.dasy")
        assert d.person() == ("Dasy", 11)
        assert d.nums(0) == 123
        assert d.nums(1) == 0
        assert d.nums(9) == 456


def test_dynarrays():
    c = compile("examples/dynamic_arrays.dasy")
    assert c.nums(0) == 1
    assert c.nums(1) == 2
    assert c.nums(2) == 3
    assert c.examples([9, 8, 7, 6, 5]) == [1, 2, 3, 9, 8, 7, 6, 5]


def test_expr_wrap():
    c = compile_src(
        """
    (defvar owner (public :address))
    (defvar nums (public (dyn-array :uint256 3)))
    (defn test [] :external
      (set self/owner msg/sender)
      (.append self/nums 1))
    """
    )
    c.test()


def test_funtions():
    c = compile("examples/functions.dasy")
    assert c.multiply(5, 10) == 50
    assert c.divide(100, 10) == 10
    assert c.multiOut() == (1, True)
    assert c.addAndSub(50, 25) == (75, 25)


def test_visibility():
    c = compile("examples/function_visibility.dasy")
    assert c.extFunc()
    assert c.sumOfSquares(2, 5) == 29
    assert c.avg(20, 80) == 50


def test_view_pure():
    c = compile("examples/view_pure.dasy")
    assert c.pureFunc(5) == 5
    assert c.viewFunc(1)
    assert c.sum(4, 5, 6) == 15
    assert c.addNum(10) == 10


def test_constants():
    c = compile("examples/constants.dasy")
    assert c.getMyConstants() == (1, 10, "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B")
    assert c.test(5) == 6


def test_immutables():
    c = compile("examples/immutable.dasy", 10)
    assert c.getMyImmutable() == 10


def test_ifelse():
    c = compile("examples/if_else.dasy")
    assert c.useCond(5) == 1
    assert c.useCond(15) == 2
    assert c.useCond(25) == 3
    assert c.absoluteValue(10, 5) == 5
    assert c.setIf(100) == 2
    assert c.setIf(1) == 1


def test_for_loop():
    c = compile("examples/for_loop.dasy")
    assert c.forLoop() == 2
    assert c.sum([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == 55


def testError():
    c = compile("examples/error.dasy")
    with boa.reverts():
        # TODO: implement checking error msg
        c.testAssert(0)
    c.testAssert(10)
    with boa.reverts():
        c.testRaise(0)
    c.testRaise(10)
    with boa.reverts():
        c.testErrorBubblesUp(0)
    c.testErrorBubblesUp(10)
    with boa.reverts():
        c.setOwner("0x0000000000000000000000000000000000000000")
    c.setOwner("0xab5801a7d398351b8be11c439e05c5b3259aec9b")
    with boa.reverts():
        c.setOwner("0xab5801a7d398351b8be11c439e05c5b3259aec9b")


def testEvent():
    c = compile("examples/event.dasy")
    c.mint(100)


def testPayable():
    c = compile("examples/payable.dasy")
    assert c.getBalance() == 0


def testHashing():
    c = compile("examples/hashing.dasy")
    assert (
        c.getMessageHash("hi")
        == b"v$w\x8d\xed\xc7_\x8b2+\x9f\xa1c*a\r@\xb8^\x10l}\x9b\xf0\xe7C\xa9\xce)\x1b\x9co"
    )


def testRawCall():
    b = compile("examples/functions.dasy")
    c = compile("examples/raw_call.dasy")
    assert c.testRawCall(b.address, 4, 3) == 12


def testDelegateCall():
    b = compile("examples/test_delegate_call.dasy")
    c = compile("examples/delegate_call.dasy")
    c.updateX(b.address, 10)
    c.updateY(b.address, 20)
    assert c.x() == 11
    assert c.y() == 400


def testInterface():
    b = compile("examples/test_interface.dasy")
    c = compile("examples/interface.dasy", b.address)
    addr1 = boa.env.generate_address()
    assert b.owner() == c.getOwner()
    c.setOwner(addr1)
    # convert addr1 to 0x formatted hex string
    assert b.owner() == addr1


def test_reentrancy():
    settings = Settings(evm_version="cancun")
    with anchor_settings(settings):
        c = compile("examples/nonreentrantenforcer.dasy")  # noqa: F841
        # v = boa.load("examples/nonreentrantenforcer.vy")
        # print("vyper settings")
        # print(v.compiler_data.settings)
        helper = compile("examples/nonreentrant2.dasy", c.address)  # noqa: F841
        with boa.reverts():
            helper.callback()


def test_auction():
    a = boa.env.generate_address()
    c = compile("examples/simple_auction.dasy", a, 100, 10000000)  # noqa: F841


def test_token():
    a = boa.env.generate_address()
    b = boa.env.generate_address()
    with boa.env.prank(a):
        t = compile("examples/ERC20.dasy", "Dasy Token", "DASY", 18, 100)
    assert t.minter() == a
    assert t.name() == "Dasy Token"
    assert t.symbol() == "DASY"
    assert t.balanceOf(a) == 100 * 10**18
    with boa.env.prank(a):
        t.transfer(b, 1 * 10**18)
        t.burn(1 * 10**18)
    assert t.balanceOf(b) == 1 * 10**18
    assert t.totalSupply() == 99 * 10**18


def test_enums():
    c = compile("examples/enum.dasy")
    assert c.getPrice() == 10
    assert c.getPriceUsingCondp() == 10


def test_in():
    c = compile_src(
        """
    (defn foo [] :bool :external
      (return (in 3 [1 2 3])))
    (defn bar [] :bool :external
      (return (notin 3 [1 2 3])))"""
    )
    assert c.foo()
    assert not c.bar()


def test_return_variable():
    c = compile_src(
        """
    (defvar x (public :uint256))
    (defn foo [] :uint256 :external
      (def x :uint256 5)
      (return x))
        """
    )


def test_usub():
    c = compile_src(
        """
        (defn foo [:int256 x] :int256 :external
            (return (usub x)))
        """
    )

    assert c.foo(10) == -10


def test_unsafe_ops():
    c = compile("examples/unsafe_ops.dasy")
    assert (
        c.unsafe_sub(0, 1)
        == 115792089237316195423570985008687907853269984665640564039457584007913129639935
    )


def test_infix():
    d = compile("examples/infix_macro.dasy")
    assert d.infix_add(10, 1) == 11
