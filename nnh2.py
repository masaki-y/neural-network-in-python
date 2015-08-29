import numpy as np
import nn
nnf = nn.NNfunc()

class NNH2(nn.NNH1):

    def __init__(self, n_units=[], filename=''):
        if filename:
            params = np.load(filename)
            self.l0 = nn.NNLayer(n_in=0, n_unit=len(params['w1']))
            self.l1 = nn.NNLayer(w=params['w1'], b=params['b1'])
            self.l2 = nn.NNLayer(w=params['w2'], b=params['b2'])
            self.l3 = nn.NNLayer(w=params['w3'], b=params['b3'])
        else:
            self.l0 = nn.NNLayer(n_in=0, n_unit=n_units[0])
            self.l1 = nn.NNLayer(n_in=n_units[0], n_unit=n_units[1])
            self.l2 = nn.NNLayer(n_in=n_units[1], n_unit=n_units[2])
            self.l3 = nn.NNLayer(n_in=n_units[2], n_unit=n_units[3])
            nn.logger.info('Net: %s' % n_units)

    def forward(self, datum, train=False):
        z0 = self.l0.input(datum[0], train)
        z1 = self.l1.forward(z0, nnf.relu, train)
        z2 = self.l2.forward(z1, nnf.relu, train)
        z3 = self.l3.forward(z2, nnf.softmax)
        loss = -np.log(z3[datum[1]])
        return z3, loss

    def backward(self, outputs, target):
        targets = np.array([1 if target == i else 0 for i in range(10)])
        delta3 = outputs - targets
        grad3w = self.grad(delta3, self.l2.z)
        delta2 = self.l2.backward(self.l3.w, delta3, nnf.d_relu)
        grad2w = self.grad(delta2, self.l1.z)
        delta1 = self.l1.backward(self.l2.w, delta2, nnf.d_relu)
        grad1w = self.grad(delta1, self.l0.z)
        return grad1w, delta1, grad2w, delta2, grad3w, delta3

    def set_dropout(self, drop_pi, drop_ph):
        if not drop_pi == 1: self.l0.set_dropout(drop_pi)
        if not drop_ph == 1:
            self.l1.set_dropout(drop_ph)
            self.l2.set_dropout(drop_ph)

    def train_batch(self, data, lr, wdecay, momentum, drop_pi, drop_ph):
        N = len(data)
        self.set_dropout(drop_pi, drop_ph)
        outputs, loss = self.forward(data[0], train=True)
        grads = self.backward(outputs, data[0][1])
        w1, b1, w2, b2, w3, b3 = \
            grads[0], grads[1], grads[2], grads[3], grads[4], grads[5]
        for n in range(1,N):
            self.set_dropout(drop_pi, drop_ph)
            outputs, loss_n = self.forward(data[n], train=True)
            loss += loss_n
            grads = self.backward(outputs, data[n][1])
            w1 += grads[0]
            b1 += grads[1]
            w2 += grads[2]
            b2 += grads[3]
            w3 += grads[4]
            b3 += grads[5]
        self.l1.update_params(w1/N, b1/N, lr, wdecay, momentum)
        self.l2.update_params(w2/N, b2/N, lr, wdecay, momentum)
        self.l3.update_params(w3/N, b3/N, lr, wdecay, momentum)
        return loss/N

    def save(self, filename):
        np.savez(filename, w1=self.l1.w, b1=self.l1.b, \
                    w2=self.l2.w, b2=self.l2.b, w3=self.l3.w, b3=self.l3.b)