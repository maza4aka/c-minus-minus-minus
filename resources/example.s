// example.s

.bss // declared variables

.comm _a, 8
.comm _b, 4

.data // constants

_nc0: .int 2

.text // assembly instructions

.globl _example

_example:

xor %rax, %rax

movl _nc0(%rip), %eax

pushq %rax
fildl (%rsp)
fstpl (%rsp)

popq %rax

movq %rax, _a(%rip)

xor %rax, %rax

movl _nc0(%rip), %eax
pushq %rax
fildl (%rsp)
fstpl (%rsp)
movq _a(%rip), %rax

pushq %rax
fldl (%rsp)
fchs
fstpl (%rsp)
popq %rax

movq %rax, __tv0(%rip)

xor %rax, %rax

movq __tv0(%rip), %rax
pushq %rax

popq %rdx
popq %rax

pushq %rdx
fldl (%rsp)
popq %rdx
pushq %rax
fldl (%rsp)

fmulp

fstpl (%rsp)
popq %rax

movq %rax, __tv1(%rip)

xor %rdx, %rdx
xor %rax, %rax

movq __tv1(%rip), %rax

pushq %rax
fldl (%rsp)
fsin
fstpl (%rsp)
popq %rax

movq %rax, __tv2(%rip)

xor %rax, %rax

movq __tv2(%rip), %rax

pushq %rax
fldl (%rsp)
fistpl (%rsp)

popq %rax

movl %eax, _b(%rip)

xor %rax, %rax

movl _nc0(%rip), %eax
pushq %rax
fildl (%rsp)
fstpl (%rsp)
movq _a(%rip), %rax

pushq %rax
fldl (%rsp)
fchs
fstpl (%rsp)
popq %rax

movq %rax, __tv3(%rip)

xor %rax, %rax

movq __tv3(%rip), %rax
pushq %rax

popq %rdx
popq %rax

pushq %rdx
fldl (%rsp)
popq %rdx
pushq %rax
fldl (%rsp)

fmulp

fstpl (%rsp)
popq %rax

movq %rax, __tv4(%rip)

xor %rdx, %rdx
xor %rax, %rax

movq __tv4(%rip), %rax

pushq %rax
fldl (%rsp)
fistpl (%rsp)

popq %rax

movl %eax, _b(%rip)

xor %rax, %rax


xor %rax, %rax /* exit code 0, no runtime errors */

retq

// temporary variables
.comm __tv0, 8
.comm __tv1, 8
.comm __tv2, 8
.comm __tv3, 8
.comm __tv4, 8

.end
